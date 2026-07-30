#!/usr/bin/env python
"""
test_chat_isolation.py - Verify per-user chat history isolation.

This script tests that:
  1. User A can create and see only their own chats.
  2. User B sees NO chats that belong to User A.
  3. User B can create their own chats.
  4. User A still sees ONLY User A's chats (not User B's).
  5. A user cannot load, rename, or delete another user's chat.
  6. Search results are scoped to the current user.

Run:  python test_chat_isolation.py
"""

import os
import sys
import tempfile

# -- Use a temporary database so we never touch real user data --
TMP_DB = os.path.join(tempfile.gettempdir(), "shani_test_isolation.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)

# Point the raw-SQLite module at the temp file BEFORE importing app code
import database
database.DATABASE_PATH = TMP_DB

# Also point the SQLAlchemy admin DB at a temp file
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}_admin.db"
os.environ["OPENROUTER_API_KEY"] = "test-key-not-real"

from werkzeug.security import generate_password_hash
from database import (
    initialize_database,
    create_user,
    create_chat,
    get_all_chats,
    load_chat,
    get_chat_title,
    get_chat_owner,
    update_chat_title,
    delete_chat,
    search_chats,
    save_message,
)

initialize_database()

PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}")


print("=" * 60)
print("CHAT ISOLATION TEST")
print("=" * 60)

# -- 1. Create two users --
print("\n1. Creating two test users...")
user_a = create_user("User A", "usera@test.com", generate_password_hash("password123"))
user_b = create_user("User B", "userb@test.com", generate_password_hash("password123"))
check("User A created with id", user_a is not None)
check("User B created with id", user_b is not None)
check("User A and B have different ids", user_a != user_b)

# -- 2. User A creates several chats --
print("\n2. User A creates several chats...")
chat_a1 = create_chat("User A - Chat 1", user_id=user_a)
chat_a2 = create_chat("User A - Chat 2", user_id=user_a)
chat_a3 = create_chat("User A - Chat 3", user_id=user_a)
save_message(chat_a1, "user", "Hello from User A in chat 1")
save_message(chat_a1, "assistant", "Hi User A!")
save_message(chat_a2, "user", "Secret User A data in chat 2")
check("User A created 3 chats", chat_a1 and chat_a2 and chat_a3)

# -- 3. User B should see NO chats --
print("\n3. User B should see NO chats...")
b_chats_initial = get_all_chats(user_b)
check("User B sees zero chats initially", len(b_chats_initial) == 0)

# -- 4. User B cannot load User A's chats --
print("\n4. User B cannot access User A's chats...")
b_loading_a1 = load_chat(chat_a1, user_b)
check("User B cannot load User A's chat messages", len(b_loading_a1) == 0)

b_title_a1 = get_chat_title(chat_a1, user_b)
check("User B cannot read User A's chat title", b_title_a1 is None)

b_owner_a1 = get_chat_owner(chat_a1)
check("get_chat_owner returns User A for chat_a1", b_owner_a1 == user_a)

# -- 5. User B cannot rename or delete User A's chats --
print("\n5. User B cannot rename or delete User A's chats...")
update_chat_title(chat_a1, "HACKED BY B", user_b)
a_title_after = get_chat_title(chat_a1, user_a)
check("User B cannot rename User A's chat", a_title_after == "User A - Chat 1")

deleted_by_b = delete_chat(chat_a1, user_b)
check("User B cannot delete User A's chat", deleted_by_b is False)
check("User A's chat still exists after B's delete attempt",
      get_chat_title(chat_a1, user_a) == "User A - Chat 1")

# -- 6. User B creates their own chats --
print("\n6. User B creates their own chats...")
chat_b1 = create_chat("User B - Chat 1", user_id=user_b)
chat_b2 = create_chat("User B - Chat 2", user_id=user_b)
save_message(chat_b1, "user", "Hello from User B in chat 1")
save_message(chat_b1, "assistant", "Hi User B!")
save_message(chat_b2, "user", "Private User B data")
check("User B created 2 chats", chat_b1 and chat_b2)

# -- 7. User B sees ONLY their own chats --
print("\n7. User B sees ONLY their own chats...")
b_chats = get_all_chats(user_b)
b_titles = [c["title"] for c in b_chats]
check("User B sees exactly 2 chats", len(b_chats) == 2)
check("User B's chats do not include User A's chats",
      "User A" not in " ".join(b_titles))
check("User B sees their own chat titles",
      "User B - Chat 1" in b_titles and "User B - Chat 2" in b_titles)

# -- 8. User A sees ONLY their own chats --
print("\n8. User A sees ONLY their own chats...")
a_chats = get_all_chats(user_a)
a_titles = [c["title"] for c in a_chats]
check("User A sees exactly 3 chats", len(a_chats) == 3)
check("User A's chats do not include User B's chats",
      "User B" not in " ".join(a_titles))
check("User A sees their own chat titles",
      "User A - Chat 1" in a_titles and "User A - Chat 2" in a_titles)

# -- 9. Search is user-scoped --
print("\n9. Search is scoped per user...")
# User A searches for "Secret" (only in User A's chat 2)
a_search = search_chats("Secret", user_a)
check("User A search finds their own 'Secret' chat", len(a_search) == 1)
check("User A search result is their own chat", a_search[0]["id"] == chat_a2)

# User B searches for "Secret" -- should find nothing
b_search = search_chats("Secret", user_b)
check("User B search finds nothing from User A", len(b_search) == 0)

# User B searches for "Private" (only in User B's chat 2)
b_search2 = search_chats("Private", user_b)
check("User B search finds their own 'Private' chat", len(b_search2) == 1)
check("User B search result is their own chat", b_search2[0]["id"] == chat_b2)

# User A searches for "Private" -- should find nothing
a_search2 = search_chats("Private", user_a)
check("User A search finds nothing from User B", len(a_search2) == 0)

# -- 10. User A can delete their own chat --
print("\n10. User A can delete their own chat...")
deleted_by_a = delete_chat(chat_a3, user_a)
check("User A can delete their own chat", deleted_by_a is True)
a_chats_after = get_all_chats(user_a)
check("User A now has 2 chats after deletion", len(a_chats_after) == 2)

# -- Summary --
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)

if FAIL > 0:
    print("\n[FAILED] CHAT ISOLATION TEST FAILED - privacy bug still present!")
    sys.exit(1)
else:
    print("\n[PASSED] CHAT ISOLATION TEST PASSED - each user sees only their own chats.")
    sys.exit(0)