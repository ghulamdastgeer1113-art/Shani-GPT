"""
models.py — SQLAlchemy database models for Shani GPT
====================================================
Purpose:
- Replace raw SQLite with Flask-SQLAlchemy ORM
- Define User, Chat, Feedback models for the admin dashboard
- Connect existing users and chats to the new system
- Store like/dislike feedback persistently

Usage:
    from models import db, User, Chat, Feedback

    # Create tables:
    db.create_all()  # called in app.py after app is configured

Tables:
    User     - id, username, email, password_hash, role, created_at
    Chat     - id, user_id, user_message, ai_response, created_at
    Feedback - id, user_id, chat_id, feedback_type, created_at
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """Registered user account with role-based access control."""
    __tablename__ = "users_sa"  # "sa" suffix to avoid clash with raw-SQLite "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # "user" or "admin"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    chats = db.relationship("Chat", backref="user", lazy="dynamic")
    feedbacks = db.relationship("Feedback", backref="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Chat(db.Model):
    """
    Stores each user-AI exchange as a single row.
    This is different from the raw-SQLite 'messages' table which stores
    individual role/content pairs. Here each row is one user message + its AI response.
    """
    __tablename__ = "chats_sa"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users_sa.id"), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    feedbacks = db.relationship("Feedback", backref="chat", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_message": self.user_message,
            "ai_response": self.ai_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Feedback(db.Model):
    """
    Stores like/dislike feedback on AI responses.
    One feedback row per user per chat message (user can update their vote).
    """
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users_sa.id"), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats_sa.id"), nullable=False)
    feedback_type = db.Column(db.String(10), nullable=False)  # "like" or "dislike"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure one feedback per user per chat (upsert logic in the route)
    __table_args__ = (
        db.UniqueConstraint("user_id", "chat_id", name="uq_user_chat_feedback"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "feedback_type": self.feedback_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }