# Shani GPT

Shani GPT is a Flask-based AI assistant that supports conversational chat, chat history, file uploads, and streamed responses via OpenRouter. The project preserves the current UI design while improving maintainability, accessibility, and deployment readiness.

## Features

- AI chat powered by OpenRouter
- Chat history sidebar with conversation loading
- New chat creation and chat deletion
- File upload support for text extraction (`txt`, `csv`, `docx`, `pdf`)
- Image upload OCR support
- Streamed assistant responses for a fluid chat experience
- Mobile-friendly sidebar and input experience

## Screenshots

> Placeholder: add screenshots here later

## Folder structure

```text
my ai chatbot/
├── app.py
├── chatbot.py
├── database.py
├── requirements.txt
├── Procfile
├── README.md
├── LICENSE
├── .env.example
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   ├── responsive.css
│   │   └── style.css
│   └── js/
│       └── chat.js
├── tests/
│   ├── test_database.py
│   └── test_utils.py
├── uploads/
├── chat.db
└── test_db.py
```

## Technologies used

- Python 3.11+
- Flask
- OpenAI / OpenRouter API
- SQLite
- HTML / CSS / JavaScript

## Installation

1. Clone the repository.
2. Create a Python virtual environment.
3. Install dependencies.

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running locally

1. Copy `.env.example` to `.env`.
2. Add your `OPENROUTER_API_KEY`.
3. Start the Flask app.

```bash
python app.py
```

4. Open `http://127.0.0.1:5000`

## Environment variables

- `OPENROUTER_API_KEY` - required API key for OpenRouter
- `FLASK_DEBUG` - optional debug flag (`1` or `0`)
- `PORT` - optional port override for deployments

## Deployment

The app is configured for lightweight deployment platforms such as Railway. The `Procfile` starts Waitress with `app:app`, and the project includes `.env.example` and `.gitignore` for best practices.

Before deploying, add `OPENROUTER_API_KEY` as a secret/environment variable in the hosting provider. Its value must be the actual key, not a template such as `${{shared.OPENROUTER_API_KEY}}` unless the provider has a shared variable with that exact name configured. Do not commit `.env` or paste the key into source code.

## Railway deployment

1. Add the repository to Railway.
2. Configure the secret `OPENROUTER_API_KEY` with the newly generated key.
3. Use the `Procfile` start command, or set the start command to `waitress-serve --listen=0.0.0.0:$PORT app:app`.
4. Deploy.

## GitHub setup

1. Add the project to a GitHub repository.
2. Commit the project files.
3. Keep `.env` out of source control and use `.env.example` instead.

## Usage

- Use the sidebar to open existing conversations.
- Click **New Chat** to start a fresh conversation.
- Type a message and press **Enter** or click the send button.
- Upload a supported document or image to let Shani GPT process text.

## Future roadmap

- Add richer image generation support
- Add user session isolation for multi-user support
- Add better message metadata and attachments view
- Add end-to-end tests for Flask routes

## License

This project is licensed under the MIT License.

## Author

Shani GPT

## Version

1.0.0
