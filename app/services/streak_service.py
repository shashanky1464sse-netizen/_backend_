from datetime import datetime, timedelta, date
from sqlalchemy import func
from app.database import db
from app.models.interview import Interview

def get_interview_streak(user_id: int) -> int:
    """
    Calculate the number of consecutive days the user has completed at least one interview,
    ending either today or yesterday (UTC).
    
    NOTE: All datetimes are stored as UTC in the database. The streak counts UTC calendar days.
    If users are in IST (UTC+5:30), an interview at 2AM IST = 8:30PM previous UTC day.
    This means IST users' late-night sessions may count for the previous UTC day.
    Keeping UTC consistently avoids timezone-related bugs across the stack.
    """
    # Fetch all interview dates for the user
    interviews = (
        db.session.query(Interview.created_at)
        .filter(Interview.user_id == user_id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    
    if not interviews:
        return 0
        
    # Extract unique UTC date objects
    unique_dates = []
    seen = set()
    for (created_at,) in interviews:
        if isinstance(created_at, str):
            try:
                d = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
            except ValueError:
                d = datetime.strptime(created_at.split()[0], "%Y-%m-%d").date()
        else:
            d = created_at.date()
            
        if d not in seen:
            seen.add(d)
            unique_dates.append(d)

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    # If the user hasn't practiced today OR yesterday, their current streak is broken (0)
    if unique_dates[0] != today and unique_dates[0] != yesterday:
        return 0

    streak = 0
    current_check_date = unique_dates[0] # either today or yesterday
    
    for interview_date in unique_dates:
        if interview_date == current_check_date:
            streak += 1
            current_check_date -= timedelta(days=1)
        else:
            break
            
    return streak

def get_week_activity(user_id: int) -> list[dict[str, bool | str]]:
    """
    Returns an array representing the last 7 days (including today),
    indicating whether the user completed an interview on each day.
    Example: [{"day": "M", "completed": True}, ...]
    """
    today = datetime.utcnow().date()
    
    # We want 7 days, ending today.
    last_7_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    start_date = last_7_dates[0]
    
    # Fetch all and filter in python to avoid func.date mismatch across SQL dialects
    interviews = (
        db.session.query(Interview.created_at)
        .filter(Interview.user_id == user_id)
        .all()
    )
    
    completed_dates = set()
    for (created_at,) in interviews:
        if isinstance(created_at, str):
            try:
                d = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
            except ValueError:
                d = datetime.strptime(created_at.split()[0], "%Y-%m-%d").date()
        else:
            d = created_at.date()
        
        if d >= start_date:
            completed_dates.add(d)
    
    def get_day_letter(d: date) -> str:
        return d.strftime("%A")[0]

    week_activity = []
    for d in last_7_dates:
        week_activity.append({
            "day": get_day_letter(d),
            "completed": d in completed_dates
        })
        
    return week_activity

