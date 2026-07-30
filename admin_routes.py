"""
admin_routes.py — Admin Panel Blueprint for Shani GPT
=====================================================
Purpose:
- Provide a secure admin dashboard area
- Protect all admin routes with role-based access
- Display live statistics and analytics from the database
- User management, chat history, and feedback views

Routes:
    /admin              -> Redirects to /admin/dashboard
    /admin/dashboard    -> Analytics dashboard with charts
    /admin/users        -> User list with search, sort, pagination
    /admin/users/<id>   -> User profile with recent activity
    /admin/chats        -> Chat list with search, filters, pagination
    /admin/chats/<id>   -> Chat detail view
    /admin/feedback     -> Feedback overview with stats
    /admin/analytics    -> Advanced analytics page
    /admin/settings     -> Coming Soon
"""

from flask import Blueprint, render_template, session, redirect, url_for, abort, request, jsonify, Response
from models import db, User as UserSA, Chat as ChatSA, Feedback as FeedbackSA
from datetime import datetime, timedelta
import csv
import io

# Create the admin blueprint with a URL prefix
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates/admin",
    static_folder="static/admin",
    static_url_path="/static/admin",
)


def admin_required(f):
    """
    Decorator that checks if the current user is authenticated AND has role='admin'.
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        user_email = session.get("user_email", "")
        sa_user = UserSA.query.filter_by(email=user_email).first()

        if not sa_user or sa_user.role != "admin":
            return render_template("admin/403.html"), 403

        return f(*args, **kwargs)

    return decorated_function


# ─── Helper Functions ──────────────────────────────────────────────────────

def get_date_range(days):
    """Get start date for filtering."""
    return datetime.utcnow() - timedelta(days=days)


def get_dashboard_stats(days=30):
    """Calculate live statistics for the dashboard cards."""
    start_date = get_date_range(days)
    today = datetime.utcnow().date()
    week_ago = get_date_range(7)
    month_ago = get_date_range(30)

    # User stats
    total_users = UserSA.query.count()
    active_today = UserSA.query.join(ChatSA).filter(
        db.func.date(ChatSA.created_at) == today
    ).distinct().count()
    new_this_week = UserSA.query.filter(UserSA.created_at >= week_ago).count()
    new_this_month = UserSA.query.filter(UserSA.created_at >= month_ago).count()

    # Chat stats
    total_chats = ChatSA.query.count()
    chats_today = ChatSA.query.filter(db.func.date(ChatSA.created_at) == today).count()
    chats_this_week = ChatSA.query.filter(ChatSA.created_at >= week_ago).count()
    chats_this_month = ChatSA.query.filter(ChatSA.created_at >= month_ago).count()

    # Feedback stats
    total_likes = FeedbackSA.query.filter_by(feedback_type="like").count()
    total_dislikes = FeedbackSA.query.filter_by(feedback_type="dislike").count()
    total_feedback = total_likes + total_dislikes
    like_ratio = (total_likes / total_feedback * 100) if total_feedback > 0 else 0
    dislike_ratio = (total_dislikes / total_feedback * 100) if total_feedback > 0 else 0

    # Averages
    avg_chats_per_user = (total_chats / total_users) if total_users > 0 else 0
    avg_response_length = db.session.query(db.func.avg(db.func.length(ChatSA.ai_response))).scalar() or 0
    avg_prompt_length = db.session.query(db.func.avg(db.func.length(ChatSA.user_message))).scalar() or 0

    return {
        "total_users": total_users,
        "active_today": active_today,
        "new_this_week": new_this_week,
        "new_this_month": new_this_month,
        "total_chats": total_chats,
        "chats_today": chats_today,
        "chats_this_week": chats_this_week,
        "chats_this_month": chats_this_month,
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "like_ratio": round(like_ratio, 1),
        "dislike_ratio": round(dislike_ratio, 1),
        "avg_chats_per_user": round(avg_chats_per_user, 1),
        "avg_response_length": round(avg_response_length, 0),
        "avg_prompt_length": round(avg_prompt_length, 0),
    }


def get_chart_data(days=30):
    """Get data for charts."""
    start_date = get_date_range(days)
    
    # Daily chats for last 30 days
    daily_chats = db.session.query(
        db.func.date(ChatSA.created_at).label('date'),
        db.func.count(ChatSA.id).label('count')
    ).filter(ChatSA.created_at >= start_date).group_by(
        db.func.date(ChatSA.created_at)
    ).order_by(db.func.date(ChatSA.created_at)).all()
    
    # Daily new users
    daily_users = db.session.query(
        db.func.date(UserSA.created_at).label('date'),
        db.func.count(UserSA.id).label('count')
    ).filter(UserSA.created_at >= start_date).group_by(
        db.func.date(UserSA.created_at)
    ).order_by(db.func.date(UserSA.created_at)).all()
    
    # Likes vs dislikes per day
    daily_feedback = db.session.query(
        db.func.date(FeedbackSA.created_at).label('date'),
        FeedbackSA.feedback_type,
        db.func.count(FeedbackSA.id).label('count')
    ).filter(FeedbackSA.created_at >= start_date).group_by(
        db.func.date(FeedbackSA.created_at),
        FeedbackSA.feedback_type
    ).order_by(db.func.date(FeedbackSA.created_at)).all()
    
    # Chats per hour
    chats_per_hour = db.session.query(
        db.func.strftime('%H', ChatSA.created_at).label('hour'),
        db.func.count(ChatSA.id).label('count')
    ).filter(ChatSA.created_at >= start_date).group_by(
        db.func.strftime('%H', ChatSA.created_at)
    ).order_by('hour').all()
    
    # Top active users
    top_users = db.session.query(
        UserSA.username,
        db.func.count(ChatSA.id).label('chat_count'),
        db.func.count(db.func.distinct(FeedbackSA.id)).label('feedback_count')
    ).join(ChatSA, UserSA.id == ChatSA.user_id).outerjoin(
        FeedbackSA, FeedbackSA.chat_id == ChatSA.id
    ).group_by(UserSA.id).order_by(
        db.func.count(ChatSA.id).desc()
    ).limit(10).all()
    
    return {
        "daily_chats": [{"date": str(d.date), "count": d.count} for d in daily_chats],
        "daily_users": [{"date": str(d.date), "count": d.count} for d in daily_users],
        "daily_feedback": [
            {"date": str(d.date), "type": d.feedback_type, "count": d.count} 
            for d in daily_feedback
        ],
        "chats_per_hour": [{"hour": int(d.hour), "count": d.count} for d in chats_per_hour],
        "top_users": [
            {
                "username": u.username,
                "chats": u.chat_count,
                "feedback": u.feedback_count
            } for u in top_users
        ],
    }


def get_most_asked_questions(limit=20):
    """Get most repeated prompts."""
    # Group by exact match for simplicity
    results = db.session.query(
        ChatSA.user_message,
        db.func.count(ChatSA.id).label('times_asked'),
        db.func.max(ChatSA.created_at).label('last_asked'),
        db.func.count(db.func.distinct(ChatSA.user_id)).label('user_count')
    ).group_by(ChatSA.user_message).order_by(
        db.func.count(ChatSA.id).desc()
    ).limit(limit).all()
    
    return [
        {
            "prompt": r.user_message,
            "times_asked": r.times_asked,
            "last_asked": r.last_asked.strftime('%Y-%m-%d %H:%M') if r.last_asked else 'N/A',
            "user_count": r.user_count
        } for r in results
    ]


def get_most_active_users(limit=10):
    """Get top 10 most active users."""
    users = db.session.query(
        UserSA.username,
        db.func.count(ChatSA.id).label('chat_count'),
        db.func.sum(db.func.case([(FeedbackSA.feedback_type == 'like', 1)], else_=0)).label('likes'),
        db.func.sum(db.func.case([(FeedbackSA.feedback_type == 'dislike', 1)], else_=0)).label('dislikes'),
        UserSA.created_at.label('join_date'),
        db.func.max(ChatSA.created_at).label('last_activity')
    ).join(ChatSA, UserSA.id == ChatSA.user_id).outerjoin(
        FeedbackSA, FeedbackSA.chat_id == ChatSA.id
    ).group_by(UserSA.id).order_by(
        db.func.count(ChatSA.id).desc()
    ).limit(limit).all()
    
    return [
        {
            "username": u.username,
            "chats": u.chat_count,
            "likes": u.likes or 0,
            "dislikes": u.dislikes or 0,
            "join_date": u.join_date.strftime('%Y-%m-%d') if u.join_date else 'N/A',
            "last_activity": u.last_activity.strftime('%Y-%m-%d %H:%M') if u.last_activity else 'N/A'
        } for u in users
    ]


def get_recent_activity(limit=20):
    """Get recent activity feed."""
    activities = []
    
    # Recent chats
    recent_chats = ChatSA.query.order_by(ChatSA.created_at.desc()).limit(10).all()
    for chat in recent_chats:
        user = UserSA.query.get(chat.user_id)
        activities.append({
            "type": "chat",
            "message": f"{user.username if user else 'Unknown'} sent a message",
            "timestamp": chat.created_at
        })
    
    # Recent feedback
    recent_feedback = FeedbackSA.query.order_by(FeedbackSA.created_at.desc()).limit(10).all()
    for fb in recent_feedback:
        user = UserSA.query.get(fb.user_id)
        action = "liked" if fb.feedback_type == "like" else "disliked"
        activities.append({
            "type": "feedback",
            "message": f"{user.username if user else 'Unknown'} {action} a response",
            "timestamp": fb.created_at
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)
    
    return activities[:limit]


def get_model_performance():
    """Get model performance metrics."""
    # Response length stats
    response_lengths = db.session.query(
        db.func.avg(db.func.length(ChatSA.ai_response)).label('avg'),
        db.func.max(db.func.length(ChatSA.ai_response)).label('max'),
        db.func.min(db.func.length(ChatSA.ai_response)).label('min')
    ).first()
    
    # Prompt length stats
    prompt_lengths = db.session.query(
        db.func.avg(db.func.length(ChatSA.user_message)).label('avg'),
        db.func.max(db.func.length(ChatSA.user_message)).label('max'),
        db.func.min(db.func.length(ChatSA.user_message)).label('min')
    ).first()
    
    return {
        "avg_response_length": round(response_lengths.avg or 0, 0),
        "max_response_length": response_lengths.max or 0,
        "min_response_length": response_lengths.min or 0,
        "avg_prompt_length": round(prompt_lengths.avg or 0, 0),
        "max_prompt_length": prompt_lengths.max or 0,
        "min_prompt_length": prompt_lengths.min or 0,
    }


def get_feedback_analytics():
    """Get feedback analytics."""
    total_likes = FeedbackSA.query.filter_by(feedback_type="like").count()
    total_dislikes = FeedbackSA.query.filter_by(feedback_type="dislike").count()
    total_feedback = total_likes + total_dislikes
    
    # Responses without feedback
    total_chats = ChatSA.query.count()
    no_feedback = total_chats - total_feedback
    
    # Most liked responses
    most_liked = db.session.query(
        ChatSA.user_message,
        ChatSA.ai_response,
        db.func.count(FeedbackSA.id).label('like_count')
    ).join(FeedbackSA).filter(
        FeedbackSA.feedback_type == 'like'
    ).group_by(ChatSA.id).order_by(
        db.func.count(FeedbackSA.id).desc()
    ).limit(5).all()
    
    # Most disliked responses
    most_disliked = db.session.query(
        ChatSA.user_message,
        ChatSA.ai_response,
        db.func.count(FeedbackSA.id).label('dislike_count')
    ).join(FeedbackSA).filter(
        FeedbackSA.feedback_type == 'dislike'
    ).group_by(ChatSA.id).order_by(
        db.func.count(FeedbackSA.id).desc()
    ).limit(5).all()
    
    return {
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "no_feedback": no_feedback,
        "like_percentage": round((total_likes / total_feedback * 100) if total_feedback > 0 else 0, 1),
        "dislike_percentage": round((total_dislikes / total_feedback * 100) if total_feedback > 0 else 0, 1),
        "most_liked": [
            {
                "prompt": m.user_message[:100],
                "response": m.ai_response[:100],
                "likes": m.like_count
            } for m in most_liked
        ],
        "most_disliked": [
            {
                "prompt": m.user_message[:100],
                "response": m.ai_response[:100],
                "dislikes": m.dislike_count
            } for m in most_disliked
        ]
    }


def get_user_activity(days=30):
    """Get user activity metrics."""
    start_date = get_date_range(days)
    
    # Daily active users
    daily_active = db.session.query(
        db.func.date(ChatSA.created_at).label('date'),
        db.func.count(db.func.distinct(ChatSA.user_id)).label('users')
    ).filter(ChatSA.created_at >= start_date).group_by(
        db.func.date(ChatSA.created_at)
    ).order_by(db.func.date(ChatSA.created_at)).all()
    
    # Weekly active users
    week_start = get_date_range(7)
    weekly_active = db.session.query(
        db.func.count(db.func.distinct(ChatSA.user_id))
    ).filter(ChatSA.created_at >= week_start).scalar()
    
    # Monthly active users
    monthly_active = db.session.query(
        db.func.count(db.func.distinct(ChatSA.user_id))
    ).filter(ChatSA.created_at >= start_date).scalar()
    
    # Average chats per day
    total_chats = ChatSA.query.filter(ChatSA.created_at >= start_date).count()
    avg_chats_per_day = total_chats / days if days > 0 else 0
    
    return {
        "daily_active": [{"date": str(d.date), "users": d.users} for d in daily_active],
        "weekly_active": weekly_active,
        "monthly_active": monthly_active,
        "avg_chats_per_day": round(avg_chats_per_day, 1),
    }


def get_system_health():
    """Get system health metrics."""
    import os
    import time
    
    # Database stats
    db_path = os.path.join(os.path.dirname(__file__), "shani_admin.db")
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    # Count records
    total_users = UserSA.query.count()
    total_chats = ChatSA.query.count()
    total_feedback = FeedbackSA.query.count()
    total_records = total_users + total_chats + total_feedback
    
    # App uptime (approximate)
    uptime = time.time() - start_time if 'start_time' in globals() else 0
    
    return {
        "db_size": f"{db_size / 1024 / 1024:.2f} MB",
        "total_records": total_records,
        "uptime": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
        "environment": "Development" if os.getenv("FLASK_DEBUG") == "1" else "Production"
    }


# Track app start time
import time
start_time = time.time()


# ─── Admin Routes ─────────────────────────────────────────────────────────


@admin_bp.route("/")
@admin_bp.route("")
def admin_index():
    """Redirect /admin to the dashboard."""
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Main admin dashboard with live statistics and charts."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()
    stats = get_dashboard_stats()
    chart_data = get_chart_data()
    
    return render_template(
        "admin/dashboard.html",
        admin_user=sa_user,
        active_page="dashboard",
        stats=stats,
        chart_data=chart_data,
    )


@admin_bp.route("/analytics")
@admin_required
def analytics():
    """Advanced analytics page with detailed charts and metrics."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()
    
    days = request.args.get("days", 30, type=int)
    chart_data = get_chart_data(days)
    most_asked = get_most_asked_questions()
    most_active = get_most_active_users()
    recent_activity = get_recent_activity()
    model_perf = get_model_performance()
    feedback_analytics = get_feedback_analytics()
    user_activity = get_user_activity(days)
    system_health = get_system_health()
    
    return render_template(
        "admin/analytics.html",
        admin_user=sa_user,
        active_page="analytics",
        days=days,
        chart_data=chart_data,
        most_asked=most_asked,
        most_active=most_active,
        recent_activity=recent_activity,
        model_perf=model_perf,
        feedback_analytics=feedback_analytics,
        user_activity=user_activity,
        system_health=system_health,
    )


@admin_bp.route("/export/<data_type>")
@admin_required
def export_data(data_type):
    """Export analytics data as CSV."""
    if data_type not in ["chats", "users", "feedback"]:
        return jsonify({"error": "Invalid export type"}), 400
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if data_type == "chats":
        writer.writerow(["Chat ID", "Username", "User Message", "AI Response", "Timestamp", "Feedback"])
        chats = ChatSA.query.join(UserSA).all()
        for chat in chats:
            feedback = FeedbackSA.query.filter_by(chat_id=chat.id).first()
            writer.writerow([
                chat.id,
                chat.user.username if chat.user else "Unknown",
                chat.user_message,
                chat.ai_response,
                chat.created_at.strftime('%Y-%m-%d %H:%M:%S') if chat.created_at else 'N/A',
                feedback.feedback_type if feedback else "None"
            ])
    
    elif data_type == "users":
        writer.writerow(["User ID", "Username", "Email", "Role", "Date Joined", "Total Chats", "Likes", "Dislikes"])
        users = UserSA.query.all()
        for user in users:
            chat_count = ChatSA.query.filter_by(user_id=user.id).count()
            likes = FeedbackSA.query.filter_by(user_id=user.id, feedback_type="like").count()
            dislikes = FeedbackSA.query.filter_by(user_id=user.id, feedback_type="dislike").count()
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.role,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A',
                chat_count,
                likes,
                dislikes
            ])
    
    elif data_type == "feedback":
        writer.writerow(["Feedback ID", "Username", "Prompt", "Feedback Type", "Date"])
        feedbacks = FeedbackSA.query.join(UserSA).join(ChatSA).all()
        for fb in feedbacks:
            writer.writerow([
                fb.id,
                fb.user.username if fb.user else "Unknown",
                fb.chat.user_message if fb.chat else "N/A",
                fb.feedback_type,
                fb.created_at.strftime('%Y-%m-%d %H:%M:%S') if fb.created_at else 'N/A'
            ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={data_type}_export.csv"}
    )


# ─── Keep existing routes ─────────────────────────────────────────────────

@admin_bp.route("/users")
@admin_required
def users():
    """User management page with search, sort, and pagination."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()

    page = request.args.get("page", 1, type=int)
    per_page = 20
    search_query = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "newest")

    query = UserSA.query

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                UserSA.username.ilike(search_pattern),
                UserSA.email.ilike(search_pattern),
            )
        )

    if sort_by == "oldest":
        query = query.order_by(UserSA.created_at.asc())
    elif sort_by == "username_asc":
        query = query.order_by(UserSA.username.asc())
    elif sort_by == "username_desc":
        query = query.order_by(UserSA.username.desc())
    else:
        query = query.order_by(UserSA.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    users_data = []
    for user in users:
        chat_count = ChatSA.query.filter_by(user_id=user.id).count()
        likes = FeedbackSA.query.filter_by(user_id=user.id, feedback_type="like").count()
        dislikes = FeedbackSA.query.filter_by(user_id=user.id, feedback_type="dislike").count()
        users_data.append({
            "user": user,
            "chat_count": chat_count,
            "likes": likes,
            "dislikes": dislikes,
        })

    return render_template(
        "admin/users.html",
        admin_user=sa_user,
        active_page="users",
        users_data=users_data,
        pagination=pagination,
        search_query=search_query,
        sort_by=sort_by,
    )


@admin_bp.route("/users/<int:user_id>")
@admin_required
def user_profile(user_id):
    """User profile page with recent activity."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()

    profile_user = UserSA.query.get_or_404(user_id)

    total_chats = ChatSA.query.filter_by(user_id=user_id).count()
    total_likes = FeedbackSA.query.filter_by(user_id=user_id, feedback_type="like").count()
    total_dislikes = FeedbackSA.query.filter_by(user_id=user_id, feedback_type="dislike").count()

    recent_chats = ChatSA.query.filter_by(user_id=user_id).order_by(
        ChatSA.created_at.desc()
    ).limit(10).all()

    chats_with_feedback = []
    for chat in recent_chats:
        feedback = FeedbackSA.query.filter_by(chat_id=chat.id).first()
        chats_with_feedback.append({
            "chat": chat,
            "feedback": feedback,
        })

    return render_template(
        "admin/user_profile.html",
        admin_user=sa_user,
        active_page="users",
        profile_user=profile_user,
        total_chats=total_chats,
        total_likes=total_likes,
        total_dislikes=total_dislikes,
        recent_chats=chats_with_feedback,
    )


@admin_bp.route("/chats")
@admin_required
def chats():
    """Chat history page with search, filters, and pagination."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()

    page = request.args.get("page", 1, type=int)
    per_page = 20
    search_query = request.args.get("search", "").strip()
    date_filter = request.args.get("date", "all")

    query = ChatSA.query.join(UserSA, ChatSA.user_id == UserSA.id)

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                UserSA.username.ilike(search_pattern),
                ChatSA.user_message.ilike(search_pattern),
            )
        )

    if date_filter == "today":
        today = datetime.utcnow().date()
        query = query.filter(db.func.date(ChatSA.created_at) == today)
    elif date_filter == "week":
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(ChatSA.created_at >= week_ago)
    elif date_filter == "month":
        month_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(ChatSA.created_at >= month_ago)

    query = query.order_by(ChatSA.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    chats = pagination.items

    chats_data = []
    for chat in chats:
        feedback = FeedbackSA.query.filter_by(chat_id=chat.id).first()
        username = UserSA.query.get(chat.user_id).username if UserSA.query.get(chat.user_id) else "Unknown"
        chats_data.append({
            "chat": chat,
            "feedback": feedback,
            "username": username,
        })

    return render_template(
        "admin/chats.html",
        admin_user=sa_user,
        active_page="chats",
        chats_data=chats_data,
        pagination=pagination,
        search_query=search_query,
        date_filter=date_filter,
    )


@admin_bp.route("/chats/<int:chat_id>")
@admin_required
def chat_detail(chat_id):
    """Chat detail page."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()

    chat = ChatSA.query.get_or_404(chat_id)
    user = UserSA.query.get(chat.user_id) if chat.user_id else None
    feedback = FeedbackSA.query.filter_by(chat_id=chat_id).first()

    return render_template(
        "admin/chat_detail.html",
        admin_user=sa_user,
        active_page="chats",
        chat=chat,
        user=user,
        feedback=feedback,
    )


@admin_bp.route("/feedback")
@admin_required
def feedback():
    """Feedback overview page with statistics and recent feedback."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()

    total_likes = FeedbackSA.query.filter_by(feedback_type="like").count()
    total_dislikes = FeedbackSA.query.filter_by(feedback_type="dislike").count()
    total_feedback = total_likes + total_dislikes

    like_percentage = (total_likes / total_feedback * 100) if total_feedback > 0 else 0
    dislike_percentage = (total_dislikes / total_feedback * 100) if total_feedback > 0 else 0

    page = request.args.get("page", 1, type=int)
    per_page = 20
    search_query = request.args.get("search", "").strip()

    query = FeedbackSA.query.join(UserSA, FeedbackSA.user_id == UserSA.id).join(
        ChatSA, FeedbackSA.chat_id == ChatSA.id
    )

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(UserSA.username.ilike(search_pattern))

    query = query.order_by(FeedbackSA.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    feedbacks = pagination.items

    feedbacks_data = []
    for fb in feedbacks:
        user = UserSA.query.get(fb.user_id)
        chat = ChatSA.query.get(fb.chat_id)
        feedbacks_data.append({
            "feedback": fb,
            "user": user,
            "chat": chat,
        })

    return render_template(
        "admin/feedback.html",
        admin_user=sa_user,
        active_page="feedback",
        total_likes=total_likes,
        total_dislikes=total_dislikes,
        like_percentage=round(like_percentage, 1),
        dislike_percentage=round(dislike_percentage, 1),
        feedbacks_data=feedbacks_data,
        pagination=pagination,
        search_query=search_query,
    )


@admin_bp.route("/settings")
@admin_required
def settings():
    """Placeholder: Settings page (Coming Soon)."""
    user_email = session.get("user_email", "")
    sa_user = UserSA.query.filter_by(email=user_email).first()

    return render_template(
        "admin/placeholder.html",
        admin_user=sa_user,
        active_page="settings",
        page_title="Settings",
    )