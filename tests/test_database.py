import os
import sqlite3

import pytest

import database
from database import (
    create_chat,
    delete_chat,
    get_all_chats,
    get_chat_title,
    initialize_database,
    load_chat,
    save_file_metadata,
    save_message,
    search_chats,
    update_chat_title,
)


def test_database_chat_lifecycle(tmp_path, monkeypatch):
    temp_db = tmp_path / "chat_test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", str(temp_db))

    initialize_database()

    chat_id = create_chat("Test Chat")
    assert isinstance(chat_id, int)
    assert get_chat_title(chat_id) == "Test Chat"

    save_message(chat_id, "user", "Hello")
    save_message(chat_id, "assistant", "Hi")

    messages = load_chat(chat_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["content"] == "Hi"

    update_chat_title(chat_id, "New Test Chat")
    assert get_chat_title(chat_id) == "New Test Chat"

    results = search_chats("Hello")
    assert any(chat["id"] == chat_id for chat in results)

    save_file_metadata(chat_id, "sample.txt", str(tmp_path / "sample.txt"), "file", "Sample text")
    delete_chat(chat_id)
    assert get_chat_title(chat_id) is None


def test_database_search_returns_empty_for_missing_term(tmp_path, monkeypatch):
    temp_db = tmp_path / "chat_search.db"
    monkeypatch.setattr(database, "DATABASE_PATH", str(temp_db))

    initialize_database()
    create_chat("Test")

    results = search_chats("nothing")
    assert results == []
