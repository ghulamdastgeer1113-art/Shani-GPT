"""
One-time script to promote a Railway user to admin.
Usage: python promote_to_admin.py your@email.com
"""
import sys
import os

# Load environment variables from .env if present
from dotenv import load_dotenv
load_dotenv()

# Ensure OPENROUTER_API_KEY is set (needed by app imports, but won't be used)
if "OPENROUTER_API_KEY" not in os.environ:
    os.environ["OPENROUTER_API_KEY"] = "dummy-for-script"

# Import the app's SQLAlchemy setup
from app import app, db
from models import User as UserSA

if len(sys.argv) != 2:
    print("Usage: python promote_to_admin.py your@email.com")
    sys.exit(1)

email = sys.argv[1].strip().lower()

with app.app_context():
    user = UserSA.query.filter_by(email=email).first()
    if not user:
        print(f"ERROR: No user found with email '{email}'")
        print("Available users:")
        for u in UserSA.query.all():
            print(f"  - {u.email} (role: {u.role})")
        sys.exit(1)

    if user.role == "admin":
        print(f"User '{email}' is already an admin. No change needed.")
        sys.exit(0)

    old_role = user.role
    user.role = "admin"
    db.session.commit()
    print(f"SUCCESS: User '{email}' promoted from '{old_role}' to 'admin'.")
    print("You can now access the admin dashboard at /admin")