import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "chat.db")


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
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

    connection.commit()
    connection.close()


def save_message(chat_id, role, content):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO messages(chat_id, role, content) VALUES(?, ?, ?)",
        (chat_id, role, content)
    )
    connection.commit()
    connection.close()


def load_chat(chat_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id",
        (chat_id,)
    )
    rows = cursor.fetchall()
    connection.close()
    return [{"role": role, "content": content} for role, content in rows]


def create_chat(title="New Chat"):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO chats(title) VALUES(?)", (title,))
    connection.commit()
    chat_id = cursor.lastrowid
    connection.close()
    return chat_id


def get_all_chats():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, title FROM chats ORDER BY id DESC")
    chats = cursor.fetchall()
    connection.close()
    return [{"id": row[0], "title": row[1]} for row in chats]


def get_chat_title(chat_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else None


def update_chat_title(chat_id, title):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE chats SET title = ? WHERE id = ?",
        (title, chat_id)
    )
    connection.commit()
    connection.close()


def delete_chat(chat_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM files WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    connection.commit()
    connection.close()


def search_chats(query):
    connection = get_connection()
    cursor = connection.cursor()
    q = f"%{query.lower()}%"
    cursor.execute("""
        SELECT DISTINCT c.id, c.title
        FROM chats c
        LEFT JOIN messages m ON c.id = m.chat_id
        WHERE LOWER(c.title) LIKE ? OR LOWER(m.content) LIKE ?
        ORDER BY c.id DESC
    """, (q, q))
    rows = cursor.fetchall()
    connection.close()
    return [{"id": row[0], "title": row[1]} for row in rows]


def save_file_metadata(chat_id, filename, filepath, file_type, extracted_text):
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