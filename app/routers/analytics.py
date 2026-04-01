from flask import Blueprint, jsonify
from app.services import analytics_service, streak_service
from app.core.security import get_current_user
from app.database import db
from app.models.interview import Interview
from app.models.user_profile import UserProfile
from sqlalchemy.orm import selectinload

bp = Blueprint('analytics', __name__)


@bp.route("/category-performance", methods=["GET"])
def get_category_performance():
    current_user = get_current_user()
    data = analytics_service.get_category_performance_data(current_user.id)
    return jsonify(data)


@bp.route("/role-consistency", methods=["GET"])
def get_role_consistency():
    current_user = get_current_user()
    data = analytics_service.analyze_role_history(current_user.id)
    return jsonify(data)


@bp.route("/summary", methods=["GET"])
def get_summary():
    """Return avg, highest, lowest, latest score and trend percentage for the current user."""
    current_user = get_current_user()
    interviews = (
        db.session.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    if not interviews:
        return jsonify({
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "latest_score": 0,
            "trend_percentage": 0.0,
            "total_sessions": 0
        })

    scores = [i.score for i in interviews]
    avg = sum(scores) / len(scores)
    latest_score = scores[0]  # Most recent is first (DESC order)

    # Trend: compare latest vs previous when < 10 sessions, else compare avg of last 5 vs prior 5
    if len(scores) >= 10:
        recent = scores[:5]
        older  = scores[5:10]
        curr_avg = sum(recent) / len(recent)
        prev_avg = sum(older) / len(older)
        trend = analytics_service.compute_trend(curr_avg, prev_avg) or 0.0
    elif len(scores) >= 2:
        trend = analytics_service.compute_trend(scores[0], scores[1]) or 0.0
    else:
        trend = 0.0

    return jsonify({
        "average_score": round(avg, 1),
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "latest_score": latest_score,
        "trend_percentage": round(trend, 2),
        "total_sessions": len(interviews)
    })


@bp.route("/last-five", methods=["GET"])
def get_last_five():
    """Return the last 5 completed interviews with score and date."""
    current_user = get_current_user()
    interviews = (
        db.session.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .limit(5)
        .all()
    )
    result = [
        {
            "id": i.id,
            "score": i.score,
            "created_at": i.created_at.strftime("%Y-%m-%dT%H:%M:%S") if i.created_at else None,
            "role_applied_for": i.role_applied_for
        }
        for i in interviews
    ]
    return jsonify(result)


@bp.route("/skills-practiced", methods=["GET"])
def get_skills_practiced():
    """Return per-category session count across all interviews."""
    current_user = get_current_user()
    interviews = (
        db.session.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .options(selectinload(Interview.skills))
        .all()
    )
    category_counts: dict[str, int] = {}
    for interview in interviews:
        for skill in interview.skills:
            cat = skill.skill_name
            # Default to 1 if total_questions_per_category is missing in older records
            count = skill.total_questions_per_category or 1
            category_counts[cat] = category_counts.get(cat, 0) + count

    result = [{"category": cat, "session_count": count}
              for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])]
    return jsonify(result)

@bp.route("/interview-streak", methods=["GET"])
def get_interview_streak():
    """Return the user's current practice streak and an array representing the last 7 days of activity."""
    current_user = get_current_user()
    streak = streak_service.get_interview_streak(current_user.id)
    week_activity = streak_service.get_week_activity(current_user.id)
    
    return jsonify({
        "current_streak": streak,
        "week_activity": week_activity
    })


@bp.route("/recent-activity", methods=["GET"])
def get_recent_activity():
    """Return a combined timeline of recent interview completions and resume uploads.
    
    Each item has:
      - type: 'interview' | 'resume'
      - date: ISO datetime string
      - score: int (interview only, else null)
      - role_applied_for: str | null (interview only)
    Sorted newest first, capped at 5 items.
    """
    current_user = get_current_user()

    # --- Interviews (last 5) ---
    interviews = (
        db.session.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .limit(5)
        .all()
    )
    events = [
        {
            "type": "interview",
            "date": i.created_at.strftime("%Y-%m-%dT%H:%M:%S") if i.created_at else None,
            "score": i.score,
            "role_applied_for": i.role_applied_for,
            "interview_id": i.id,
        }
        for i in interviews
    ]

    # --- Resume upload (last update time from user_profiles) ---
    profile = (
        db.session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id)
        .first()
    )
    # Only show resume event when skills_json is populated (resume was actually uploaded)
    if profile and profile.skills_json and profile.skills_json not in ("{}", "[]", "") and profile.updated_at:
        events.append({
            "type": "resume",
            "date": profile.updated_at.strftime("%Y-%m-%dT%H:%M:%S"),
            "score": None,
            "role_applied_for": None,
            "interview_id": None,
        })

    # Sort all events newest first, cap at 5
    events.sort(key=lambda x: x["date"] or "", reverse=True)
    return jsonify(events[:5])
