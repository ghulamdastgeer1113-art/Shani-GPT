import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "chat.db")


def get_connection():
    """Return a SQLite connection for the project database."""
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create the persistent tables for chats, messages, and uploads."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            file_type TEXT NOT NULL,
            extracted_text TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Migration: add user_id column to pre-existing chats tables ──
    # Required for per-user chat isolation (privacy fix). Existing chats
    # keep user_id = NULL so they are invisible to all users until manually
    # reassigned. New chats always receive the creating user's id.
    cursor.execute("PRAGMA table_info(chats)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in existing_columns:
        cursor.execute("ALTER TABLE chats ADD COLUMN user_id INTEGER")

    connection.commit()
    connection.close()



def save_message(chat_id, role, content):
    """Save a single role/content pair for the active chat."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO messages(chat_id, role, content) VALUES(?, ?, ?)",
        (chat_id, role, content)
    )
    connection.commit()
    connection.close()


def load_chat(chat_id, user_id):
    """Load the conversation history for a specific chat (user-scoped).

    Only returns messages if the chat belongs to the given user_id.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """SELECT m.role, m.content
           FROM messages m
           JOIN chats c ON m.chat_id = c.id
           WHERE m.chat_id = ? AND c.user_id = ?
           ORDER BY m.id""",
        (chat_id, user_id)
    )
    rows = cursor.fetchall()
    connection.close()
    return [{"role": role, "content": content} for role, content in rows]


def create_chat(title="New Chat", user_id=None):
    """Create a new chat row associated with a user and return its identifier."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO chats(title, user_id) VALUES(?, ?)", (title, user_id))
    connection.commit()
    chat_id = cursor.lastrowid
    connection.close()
    return chat_id


def get_all_chats(user_id):
    """Return all chat records belonging to a specific user, ordered by most recent."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, title FROM chats WHERE user_id = ? ORDER BY id DESC", (user_id,))
    chats = cursor.fetchall()
    connection.close()
    return [{"id": row[0], "title": row[1]} for row in chats]


def get_chat_owner(chat_id):
    """Return the user_id of the chat owner, or None if the chat doesn't exist."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else None


def get_chat_title(chat_id, user_id):
    """Return the title of a chat only if it belongs to the given user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT title FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else None


def update_chat_title(chat_id, title, user_id):
    """Update a chat's title only if it belongs to the given user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE chats SET title = ? WHERE id = ? AND user_id = ?",
        (title, chat_id, user_id)
    )
    connection.commit()
    connection.close()


def delete_chat(chat_id, user_id):
    """Delete a chat and its messages/files only if it belongs to the given user.

    Returns True if a chat was deleted, False otherwise.
    """
    connection = get_connection()
    cursor = connection.cursor()
    # Verify the chat belongs to the user before deleting
    cursor.execute("SELECT id FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
    if not cursor.fetchone():
        connection.close()
        return False
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM files WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    connection.commit()
    connection.close()
    return True


def search_chats(query, user_id):
    """Search chat titles and message content for a specific user only."""
    connection = get_connection()
    cursor = connection.cursor()
    q = f"%{query.lower()}%"
    cursor.execute("""
        SELECT DISTINCT c.id, c.title
        FROM chats c
        LEFT JOIN messages m ON c.id = m.chat_id
        WHERE c.user_id = ? AND (LOWER(c.title) LIKE ? OR LOWER(m.content) LIKE ?)
        ORDER BY c.id DESC
    """, (user_id, q, q))
    rows = cursor.fetchall()
    connection.close()
    return [{"id": row[0], "title": row[1]} for row in rows]


def save_file_metadata(chat_id, filename, filepath, file_type, extracted_text):
    """Record metadata for uploaded files and OCR/document text extracts."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO files(chat_id, filename, filepath, file_type, extracted_text) VALUES(?, ?, ?, ?, ?)",
        (chat_id, filename, filepath, file_type, extracted_text)
    )
    connection.commit()
    connection.close()


def get_chat_files(chat_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT filename, file_type, uploaded_at FROM files WHERE chat_id = ? ORDER BY id DESC",
        (chat_id,)
    )
    rows = cursor.fetchall()
    connection.close()
    return [{"filename": row[0], "file_type": row[1], "uploaded_at": row[2]} for row in rows]


def create_user(name, email, password_hash):
    """Create a new user record and return the new user's id."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users(name, email, password_hash) VALUES(?, ?, ?)",
        (name, email.lower(), password_hash)
    )
    connection.commit()
    user_id = cursor.lastrowid
    connection.close()
    return user_id


def get_user_by_email(email):
    """Return a user record dict matching the given email, or None."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (email.lower(),)
    )
    row = cursor.fetchone()
    connection.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "password_hash": row[3]}


def get_user_by_id(user_id):
    """Return a user record dict (without password hash) matching the given id, or None."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    connection.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2]}