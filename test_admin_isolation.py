#!/usr/bin/env python
"""
test_admin_isolation.py - Verify the admin dashboard still sees ALL chats
while normal users only see their own.

Run:  python test_admin_isolation.py
"""

import os
import sys
import tempfile

# -- Use a temporary database so we never touch real user data --
TMP_DB = os.path.join(tempfile.gettempdir(), "shani_admin_iso_test.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)

import database
database.DATABASE_PATH = TMP_DB

TMP_ADMIN_DB = os.path.join(tempfile.gettempdir(), "shani_admin_iso_admin.db")
if os.path.exists(TMP_ADMIN_DB):
    os.remove(TMP_ADMIN_DB)

os.environ["DATABASE_URL"] = f"sqlite:///{TMP_ADMIN_DB}"
os.environ["OPENROUTER_API_KEY"] = "test-key-not-real"

from werkzeug.security import generate_password_hash
from database import (
    initialize_database,
    create_user,
    create_chat,
    get_all_chats,
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
print("ADMIN DASHBOARD ISOLATION TEST")
print("=" * 60)

# -- 1. Create users and chats in the raw-SQLite DB (user chat UI) --
print("\n1. Setting up users and chats...")
user_a = create_user("User A", "usera@test.com", generate_password_hash("password123"))
user_b = create_user("User B", "userb@test.com", generate_password_hash("password123"))

chat_a1 = create_chat("User A - Chat 1", user_id=user_a)
chat_a2 = create_chat("User A - Chat 2", user_id=user_a)
chat_b1 = create_chat("User B - Chat 1", user_id=user_b)
save_message(chat_a1, "user", "Hello from A")
save_message(chat_b1, "user", "Hello from B")

# -- 2. Normal users see only their own chats --
print("\n2. Normal users see only their own chats...")
a_chats = get_all_chats(user_a)
b_chats = get_all_chats(user_b)
check("User A sees 2 chats", len(a_chats) == 2)
check("User B sees 1 chat", len(b_chats) == 1)
check("User A does not see User B's chats",
      all("User B" not in c["title"] for c in a_chats))
check("User B does not see User A's chats",
      all("User A" not in c["title"] for c in b_chats))

# -- 3. Admin dashboard uses SQLAlchemy (ChatSA) and sees ALL chats --
print("\n3. Admin dashboard (SQLAlchemy) sees ALL users' chats...")
from app import app
from models import db, User as UserSA, Chat as ChatSA

with app.app_context():
    # Create SA users matching the raw-SQLite users
    sa_a = UserSA(username="user_a", email="usera@test.com",
                  password_hash="x", role="user")
    sa_b = UserSA(username="user_b", email="userb@test.com",
                  password_hash="x", role="user")
    sa_admin = UserSA(username="admin", email="admin@test.com",
                      password_hash="x", role="admin")
    db.session.add_all([sa_a, sa_b, sa_admin])
    db.session.commit()

    # Create chat records in the SA model (as the app does via /save_chat_sa)
    sa_chat1 = ChatSA(user_id=sa_a.id, user_message="A msg 1", ai_response="A resp 1")
    sa_chat2 = ChatSA(user_id=sa_a.id, user_message="A msg 2", ai_response="A resp 2")
    sa_chat3 = ChatSA(user_id=sa_b.id, user_message="B msg 1", ai_response="B resp 1")
    db.session.add_all([sa_chat1, sa_chat2, sa_chat3])
    db.session.commit()

    # Admin query: ChatSA.query (no user filter) - sees ALL chats
    all_sa_chats = ChatSA.query.all()
    check("Admin sees ALL 3 chats across users", len(all_sa_chats) == 3)

    # Admin can filter by a specific user (user profile page)
    a_sa_chats = ChatSA.query.filter_by(user_id=sa_a.id).all()
    b_sa_chats = ChatSA.query.filter_by(user_id=sa_b.id).all()
    check("Admin sees User A's 2 chats", len(a_sa_chats) == 2)
    check("Admin sees User B's 1 chat", len(b_sa_chats) == 1)

    # Admin dashboard stats count all chats
    total = ChatSA.query.count()
    check("Admin dashboard total_chats = 3", total == 3)

# -- 4. Confirm admin_routes.py was NOT modified --
print("\n4. Admin routes file unchanged...")
admin_path = os.path.join(os.path.dirname(__file__), "admin_routes.py")
with open(admin_path, "r", encoding="utf-8") as f:
    admin_content = f.read()
check("admin_routes.py still queries ChatSA.query (all chats)",
      "ChatSA.query" in admin_content)
check("admin_routes.py has no user_id filtering on dashboard",
      "filter_by(user_id=session" not in admin_content)

# -- Summary --
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)

if FAIL > 0:
    print("\n[FAILED] Admin dashboard isolation test FAILED!")
    sys.exit(1)
else:
    print("\n[PASSED] Admin dashboard sees all chats; users see only their own.")
    sys.exit(0)