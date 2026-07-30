import re
from functools import wraps

from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for, flash
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os

from database import (
    initialize_database,
    save_message,
    create_chat,
    get_all_chats,
    load_chat,
    get_chat_title,
    get_chat_owner,
    update_chat_title,
    delete_chat,
    search_chats,
    save_file_metadata,
    create_user,
    get_user_by_email,
    get_user_by_id,
)
from utils import (
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    allowed_file,
    build_pollinations_url,
    clean_image_prompt,
    extract_text_from_file,
    extract_text_from_image,
    is_image_prompt,
    make_unique_filename,
)

# ─── SQLAlchemy Models (for admin dashboard data collection) ───────────────
from models import db, User as UserSA, Chat as ChatSA, Feedback as FeedbackSA

# ─── Admin Panel Blueprint ─────────────────────────────────────────────────
from admin_routes import admin_bp

def save_generated_image(chat_id: int, prompt: str, image_url: str):
    """
    Placeholder for future image metadata persistence.
    Create generated_images table later with:
    id, chat_id, prompt, image_url, created_at
    """
    pass

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limit uploads to 16MB

# ─── SQLAlchemy Configuration ──────────────────────────────────────────────
# Use SQLite for development; switch to PostgreSQL in production
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///shani_admin.db"  # Separate DB file for admin models
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Create all SQLAlchemy tables
with app.app_context():
    db.create_all()
    # Migration: add name column to users_sa table if it doesn't exist
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users_sa')]
        if 'name' not in columns:
            db.session.execute(db.text("ALTER TABLE users_sa ADD COLUMN name VARCHAR(120) NOT NULL DEFAULT ''"))
            db.session.commit()
    except Exception:
        pass  # Table might not exist yet, or column already exists

# ─── Register Admin Blueprint ──────────────────────────────────────────────
# Must be AFTER db.init_app() so admin_routes can import models
app.register_blueprint(admin_bp)

# ─── Existing raw-SQLite database initialization ──────────────────────────
initialize_database()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_FILE_EXTENSIONS = {"pdf", "docx", "txt", "csv"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

# NOTE: The previous module-level globals `current_chat` and `chat_history`
# were removed because they were shared across ALL users in the Flask process,
# causing a serious privacy bug (users could see each other's conversations).
# Chat state is now tracked per-user via the Flask session and loaded from the
# database on each request. See get_current_chat_id() below.

openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
if not openrouter_api_key or "${{" in openrouter_api_key or "}}" in openrouter_api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is required. Set the actual OpenRouter key in the deployment environment."
    )

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)


def get_current_chat_id():
    """Return the current user's active chat id from the session.

    If the user has no active chat in the session, pick their most recent chat
    from the database, or create a new one if they have none. The chosen id is
    stored back in the session so subsequent requests in the same session reuse
    it. This replaces the old shared module-level `current_chat` global.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    chat_id = session.get("current_chat_id")
    if chat_id:
        # Verify the chat still exists and belongs to this user
        owner = get_chat_owner(chat_id)
        if owner == user_id:
            return chat_id

    # No valid active chat — pick the user's most recent one
    chats = get_all_chats(user_id)
    if chats:
        chat_id = chats[0]["id"]
    else:
        chat_id = create_chat(title="Shani GPT", user_id=user_id)
    session["current_chat_id"] = chat_id
    return chat_id


def generate_chat_title(messages):
    """Generate a short chat title from the conversation history."""
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
            {"role": "user", "content": user_prompt},
        ],
    )
    title = response.choices[0].message.content.strip()
    return title[:60]


# ─── Authentication Helpers ──────────────────────────────────────────────

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def login_required(f):
    """Decorator: redirect unauthenticated users to the login page."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ─── Authentication Routes ───────────────────────────────────────────────


@app.route("/login", methods=["GET", "POST"])
def login():
    """Display login form and authenticate users."""
    # If already logged in, redirect to chat
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        # Try UserSA (SQLAlchemy) first, fall back to raw SQLite users table
        user = UserSA.query.filter_by(email=email.lower()).first()
        if not user:
            # Fallback: check the raw SQLite users table
            user = get_user_by_email(email)
            if not user or not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password. Please try again.", "error")
                return render_template("login.html")
            # Login successful with raw SQLite user
            session.permanent = True
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
        else:
            # Login successful with UserSA
            if not check_password_hash(user.password_hash, password):
                flash("Invalid email or password. Please try again.", "error")
                return render_template("login.html")
            session.permanent = True
            session["user_id"] = user.id
            session["user_name"] = user.name or user.username
            session["user_email"] = user.email
        # Clear any stale active chat from a previous session
        session.pop("current_chat_id", None)
        # Get display name (works for both UserSA objects and raw SQLite dicts)
        display_name = user.name if hasattr(user, 'name') else user.get('name', user.get('username', 'User'))
        flash(f"Welcome back, {display_name}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Display registration form and create new user accounts."""
    # If already logged in, redirect to chat
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # ── Validation ──────────────────────────────────────────────
        errors = []

        if not name:
            errors.append("Full name is required.")

        if not email:
            errors.append("Email address is required.")
        elif not EMAIL_REGEX.match(email):
            errors.append("Please enter a valid email address.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html")

        # ── Check for duplicate account (check BOTH databases) ──────
        existing = get_user_by_email(email)
        existing_sa = UserSA.query.filter_by(email=email.lower()).first()
        if existing or existing_sa:
            flash("An account with this email already exists. Please sign in.", "error")
            return render_template("register.html")

        # ── Create user ─────────────────────────────────────────────
        password_hash = generate_password_hash(password)
        user_id = create_user(name, email, password_hash)

        # Also create user in SQLAlchemy User model for admin dashboard
        with app.app_context():
            sa_user = UserSA(
                username=name.lower().replace(" ", "_"),
                name=name,
                email=email.lower(),
                password_hash=password_hash,
                role="user"
            )
            db.session.add(sa_user)
            db.session.commit()

        # Auto-login after registration
        session.permanent = True
        session["user_id"] = sa_user.id
        session["user_name"] = name
        session["user_email"] = email
        # New users start with no active chat
        session.pop("current_chat_id", None)
        flash(f"Account created successfully! Welcome, {name}!", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log the user out and clear the session."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ─── Protected Routes ────────────────────────────────────────────────────


@app.route("/")
@login_required
def index():
    # Try to get user from UserSA (SQLAlchemy) first, fall back to raw SQLite
    user = UserSA.query.get(session["user_id"])
    if not user:
        user = get_user_by_id(session["user_id"])
    user_id = session["user_id"]
    chats = get_all_chats(user_id)
    current_chat = get_current_chat_id()
    # Load this user's own conversation for the active chat
    messages = load_chat(current_chat, user_id) if current_chat else []
    return render_template(
        "index.html",
        messages=messages,
        chats=chats,
        current_chat=current_chat,
        chat_title=get_chat_title(current_chat, user_id) or "Shani GPT",
        user=user
    )

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    user_id = session["user_id"]
    current_chat = get_current_chat_id()

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Load this user's own conversation history from the database
    chat_history = load_chat(current_chat, user_id)
    chat_history.append({"role": "user", "content": message})
    save_message(current_chat, "user", message)

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=chat_history,
    )

    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})
    save_message(current_chat, "assistant", reply)

    current_title = get_chat_title(current_chat, user_id)
    if current_title in {"New Chat", "Shani GPT"}:
        title = generate_chat_title(chat_history)
        if title:
            update_chat_title(current_chat, title, user_id)

    return jsonify({"reply": reply})


@app.route("/stream", methods=["POST"])
@login_required
def stream():
    user_id = session["user_id"]
    current_chat = get_current_chat_id()

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if user_message and is_image_prompt(user_message):
        prompt = clean_image_prompt(user_message)
        image_url = build_pollinations_url(prompt)
        # TODO: save_generated_image(current_chat, prompt, image_url)
        return jsonify({"type": "image", "url": image_url, "prompt": prompt})

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Load this user's own conversation history from the database
    chat_history = load_chat(current_chat, user_id)
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

        current_title = get_chat_title(current_chat, user_id)
        if current_title in {"New Chat", "Shani GPT"}:
            title = generate_chat_title(chat_history)
            if title:
                update_chat_title(current_chat, title, user_id)

    return Response(stream_with_context(generate()), mimetype="text/plain; charset=utf-8")


@app.route("/new_chat", methods=["POST"])
@login_required
def new_chat():
    user_id = session["user_id"]
    # Create a new chat owned by the current user and make it the active one
    current_chat = create_chat(title="New Chat", user_id=user_id)
    session["current_chat_id"] = current_chat

    return jsonify({"success": True, "chat_id": current_chat})


@app.route("/load_chat/<int:chat_id>")
@login_required
def load_chat_route(chat_id):
    user_id = session["user_id"]

    # Verify the chat belongs to the current user before loading
    owner = get_chat_owner(chat_id)
    if owner != user_id:
        return jsonify({"error": "Chat not found"}), 404

    session["current_chat_id"] = chat_id
    chat_history = load_chat(chat_id, user_id)
    title = get_chat_title(chat_id, user_id) or "Shani GPT"

    return jsonify({"messages": chat_history, "title": title})


@app.route("/rename_chat", methods=["POST"])
@login_required
def rename_chat():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    chat_id = data.get("chat_id")
    title = data.get("title", "").strip()

    if not chat_id or not title:
        return jsonify({"error": "Chat ID and title are required"}), 400

    # Verify the chat belongs to the current user before renaming
    owner = get_chat_owner(chat_id)
    if owner != user_id:
        return jsonify({"error": "Chat not found"}), 404

    update_chat_title(chat_id, title, user_id)
    return jsonify({"success": True, "title": title})


@app.route("/delete_chat/<int:chat_id>", methods=["POST"])
@login_required
def delete_chat_route(chat_id):
    user_id = session["user_id"]

    # delete_chat now verifies ownership and returns False if not the owner
    deleted = delete_chat(chat_id, user_id)
    if not deleted:
        return jsonify({"error": "Chat not found"}), 404

    # If the deleted chat was the active one, clear it from the session
    if session.get("current_chat_id") == chat_id:
        session.pop("current_chat_id", None)

    remaining = get_all_chats(user_id)
    if remaining:
        current_chat = remaining[0]["id"]
        session["current_chat_id"] = current_chat
        return jsonify({"success": True, "chat_id": current_chat, "title": get_chat_title(current_chat, user_id)})
    else:
        current_chat = create_chat(title="New Chat", user_id=user_id)
        session["current_chat_id"] = current_chat
        return jsonify({"success": True, "chat_id": current_chat, "title": "New Chat"})


@app.route("/search_chats")
@login_required
def search_chats_route():
    user_id = session["user_id"]
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify(get_all_chats(user_id))
    return jsonify(search_chats(query, user_id))


@app.route("/upload_file", methods=["POST"])
@login_required
def upload_file():
    user_id = session["user_id"]
    current_chat = get_current_chat_id()

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "A valid file is required"}), 400

    if not allowed_file(file.filename, ALLOWED_FILE_EXTENSIONS):
        return jsonify({"error": "File type not supported"}), 400

    filename = file.filename
    unique_name = make_unique_filename(filename)
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

    save_message(current_chat, "assistant", assistant_text)

    return jsonify({"assistant_text": assistant_text})


@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    user_id = session["user_id"]
    current_chat = get_current_chat_id()

    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({"error": "A valid image is required"}), 400

    if not allowed_file(image.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Image type not supported"}), 400

    filename = image.filename
    unique_name = make_unique_filename(filename)
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

    save_message(current_chat, "assistant", assistant_text)

    return jsonify({"assistant_text": assistant_text})


# ─── Save Chat to SQLAlchemy (for admin dashboard) ────────────────────────

@app.route("/save_chat_sa", methods=["POST"])
@login_required
def save_chat_sa():
    """
    Store a user message + AI response pair in the SQLAlchemy Chat model.
    Called from the frontend after each AI response is received.
    This is separate from the raw-SQLite 'messages' table which stores
    individual role/content pairs for the chat UI.
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get("user_message", "").strip()
    ai_response = data.get("ai_response", "").strip()

    if not user_message or not ai_response:
        return jsonify({"error": "Both user_message and ai_response are required"}), 400

    # Get the SQLAlchemy user record for the current session user
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()
    if not sa_user:
        return jsonify({"error": "User not found in admin database"}), 404

    # Create the chat record
    chat_record = ChatSA(
        user_id=sa_user.id,
        user_message=user_message,
        ai_response=ai_response
    )
    db.session.add(chat_record)
    db.session.commit()

    return jsonify({
        "success": True,
        "chat_id": chat_record.id,
        "message": "Chat saved for admin dashboard"
    })


# ─── Feedback Endpoint (Like / Dislike) ───────────────────────────────────

@app.route("/feedback", methods=["POST"])
@login_required
def submit_feedback():
    """
    Store like/dislike feedback for an AI response.
    Uses upsert logic: if the user already submitted feedback for this chat,
    update it; otherwise create a new record.

    Request body:
        {
            "chat_id": <int>,       # The ChatSA.id from save_chat_sa
            "feedback_type": "like" | "dislike" | "none"
        }

    If feedback_type is "none", the existing feedback is deleted (toggle off).
    """
    data = request.get_json(silent=True) or {}
    chat_sa_id = data.get("chat_id")
    feedback_type = data.get("feedback_type", "").strip().lower()

    if not chat_sa_id:
        return jsonify({"error": "chat_id is required"}), 400

    if feedback_type not in ("like", "dislike", "none"):
        return jsonify({"error": "feedback_type must be 'like', 'dislike', or 'none'"}), 400

    # Get the SQLAlchemy user record
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()
    if not sa_user:
        return jsonify({"error": "User not found in admin database"}), 404

    # Verify the chat exists
    chat_record = ChatSA.query.get(chat_sa_id)
    if not chat_record:
        return jsonify({"error": "Chat record not found"}), 404

    # Upsert logic: find existing feedback or create new one
    existing_feedback = FeedbackSA.query.filter_by(
        user_id=sa_user.id,
        chat_id=chat_sa_id
    ).first()

    if feedback_type == "none":
        # Remove feedback (user toggled off)
        if existing_feedback:
            db.session.delete(existing_feedback)
            db.session.commit()
        return jsonify({"success": True, "message": "Feedback removed"})

    if existing_feedback:
        # Update existing feedback
        existing_feedback.feedback_type = feedback_type
    else:
        # Create new feedback
        new_feedback = FeedbackSA(
            user_id=sa_user.id,
            chat_id=chat_sa_id,
            feedback_type=feedback_type
        )
        db.session.add(new_feedback)

    db.session.commit()

    return jsonify({
        "success": True,
        "feedback_type": feedback_type,
        "message": f"Feedback recorded: {feedback_type}"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)