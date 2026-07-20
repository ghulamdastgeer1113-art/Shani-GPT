from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import uuid
from urllib.parse import quote
import re

from database import (
    initialize_database,
    save_message,
    create_chat,
    get_all_chats,
    load_chat,
    get_chat_title,
    update_chat_title,
    delete_chat,
    search_chats,
    save_file_metadata
)

IMAGE_KEYWORDS = [
    "generate",
    "create",
    "draw",
    "paint",
    "illustrate",
    "design",
    "image",
    "picture",
]

STOP_WORDS = [
    "an",
    "a",
    "the",
    "of",
    "for",
    "please",
    "with",
    "in",
    "on",
    "to",
    "and",
    "me",
]

def is_image_prompt(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in IMAGE_KEYWORDS)

def clean_image_prompt(text: str) -> str:
    lower = text.lower()
    lower = re.sub(r"[^a-z0-9\s]", " ", lower)
    lower = re.sub(
        r"\b(" + r"|".join(re.escape(k) for k in IMAGE_KEYWORDS) + r")\b",
        "",
        lower,
    )
    lower = re.sub(
        r"\b(" + r"|".join(re.escape(k) for k in STOP_WORDS) + r")\b",
        "",
        lower,
    )
    prompt = " ".join(lower.split()).strip()
    return prompt or text.strip()

def build_pollinations_url(prompt: str) -> str:
    return f"https://image.pollinations.ai/prompt/{quote(prompt)}"

def save_generated_image(chat_id: int, prompt: str, image_url: str):
    """
    Placeholder for future image metadata persistence.
    Create generated_images table later with:
    id, chat_id, prompt, image_url, created_at
    """
    pass

load_dotenv()

app = Flask(__name__)
initialize_database()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_FILE_EXTENSIONS = {"pdf", "docx", "txt", "csv"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

existing_chats = get_all_chats()
if existing_chats:
    current_chat = existing_chats[0]["id"]
    chat_history = load_chat(current_chat)
else:
    current_chat = create_chat(title="Shani GPT")
    chat_history = []

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def allowed_file(filename, allowed_ext):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_ext


def extract_text_from_file(filepath, filename):
    ext = filename.rsplit(".", 1)[1].lower()
    try:
        if ext in {"txt", "csv"}:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        if ext == "docx":
            import docx
            doc = docx.Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        if ext == "pdf":
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return None
    return None


def extract_text_from_image(filepath):
    try:
        from PIL import Image
        import pytesseract
        image = Image.open(filepath)
        return pytesseract.image_to_string(image)
    except Exception:
        return None


def generate_chat_title(messages):
    if not messages:
        return None
    prompt_messages = messages[:6]
    system_prompt = (
        "Create a short descriptive title for this conversation. "
        "Return just the title in 5 words or less."
    )
    user_prompt = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" for msg in prompt_messages
    )
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    title = response.choices[0].message.content.strip()
    return title[:60]


@app.route("/")
def index():
    chats = get_all_chats()
    return render_template(
        "index.html",
        messages=chat_history,
        chats=chats,
        current_chat=current_chat,
        chat_title=get_chat_title(current_chat) or "Shani GPT"
    )


@app.route("/chat", methods=["POST"])
def chat():
    global chat_history

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    chat_history.append({"role": "user", "content": message})
    save_message(current_chat, "user", message)

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=chat_history
    )

    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})
    save_message(current_chat, "assistant", reply)

    current_title = get_chat_title(current_chat)
    if current_title in {"New Chat", "Shani GPT"}:
        title = generate_chat_title(chat_history)
        if title:
            update_chat_title(current_chat, title)

    return jsonify({"reply": reply})


@app.route("/stream", methods=["POST"])
def stream():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if user_message and is_image_prompt(user_message):
        prompt = clean_image_prompt(user_message)
        image_url = build_pollinations_url(prompt)
        # TODO: save_generated_image(current_chat_id, prompt, image_url)
        return jsonify({"type": "image", "url": image_url, "prompt": prompt})

    global chat_history

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    chat_history.append({"role": "user", "content": user_message})
    save_message(current_chat, "user", user_message)

    def generate():
        full_reply = ""
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=chat_history,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_reply += text
                yield text

        chat_history.append({"role": "assistant", "content": full_reply})
        save_message(current_chat, "assistant", full_reply)

        current_title = get_chat_title(current_chat)
        if current_title in {"New Chat", "Shani GPT"}:
            title = generate_chat_title(chat_history)
            if title:
                update_chat_title(current_chat, title)

    return Response(stream_with_context(generate()), mimetype="text/plain; charset=utf-8")


@app.route("/new_chat", methods=["POST"])
def new_chat():
    global current_chat, chat_history

    current_chat = create_chat(title="New Chat")
    chat_history = []

    return jsonify({"success": True, "chat_id": current_chat})


@app.route("/load_chat/<int:chat_id>")
def load_chat_route(chat_id):
    global current_chat, chat_history

    current_chat = chat_id
    chat_history = load_chat(chat_id)
    title = get_chat_title(chat_id) or "Shani GPT"

    return jsonify({"messages": chat_history, "title": title})


@app.route("/rename_chat", methods=["POST"])
def rename_chat():
    data = request.get_json(silent=True) or {}
    chat_id = data.get("chat_id")
    title = data.get("title", "").strip()

    if not chat_id or not title:
        return jsonify({"error": "Chat ID and title are required"}), 400

    update_chat_title(chat_id, title)
    return jsonify({"success": True, "title": title})


@app.route("/delete_chat/<int:chat_id>", methods=["POST"])
def delete_chat_route(chat_id):
    global current_chat, chat_history

    delete_chat(chat_id)

    remaining = get_all_chats()
    if remaining:
        current_chat = remaining[0]["id"]
        chat_history = load_chat(current_chat)
        return jsonify({"success": True, "chat_id": current_chat, "title": get_chat_title(current_chat)})
    else:
        current_chat = create_chat(title="New Chat")
        chat_history = []
        return jsonify({"success": True, "chat_id": current_chat, "title": "New Chat"})


@app.route("/search_chats")
def search_chats_route():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify(get_all_chats())
    return jsonify(search_chats(query))


@app.route("/upload_file", methods=["POST"])
def upload_file():
    global chat_history

    file = request.files.get("file")
    if not file or not allowed_file(file.filename, ALLOWED_FILE_EXTENSIONS):
        return jsonify({"error": "File type not supported"}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(filepath)

    extracted_text = extract_text_from_file(filepath, filename)
    if not extracted_text:
        extracted_text = "No extractable text was found in this file."
    save_file_metadata(current_chat, filename, filepath, "file", extracted_text)

    assistant_text = (
        f"File uploaded: {filename}\n\n"
        f"Extracted text:\n{extracted_text}"
    )

    chat_history.append({"role": "assistant", "content": assistant_text})
    save_message(current_chat, "assistant", assistant_text)

    return jsonify({"assistant_text": assistant_text})


@app.route("/upload_image", methods=["POST"])
def upload_image():
    global chat_history

    image = request.files.get("image")
    if not image or not allowed_file(image.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Image type not supported"}), 400

    filename = secure_filename(image.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_name)
    image.save(filepath)

    extracted_text = extract_text_from_image(filepath)
    if not extracted_text:
        extracted_text = "No text was detected in the image."

    save_file_metadata(current_chat, filename, filepath, "image", extracted_text)

    assistant_text = (
        f"Image uploaded: {filename}\n\n"
        f"Extracted text:\n{extracted_text}"
    )

    chat_history.append({"role": "assistant", "content": assistant_text})
    save_message(current_chat, "assistant", assistant_text)

    return jsonify({"assistant_text": assistant_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)