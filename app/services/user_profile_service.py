import json
from app.database import db
from app.models.user_profile import UserProfile
from app.services.resume_service import ROLE_KEYWORDS

def update_user_profile(
    user_id: int,
    skills: dict,
    target_role: str | None,
    experience_years: int | None = None,
    experience_level: str | None = None,
    preferred_difficulty: str | None = None
) -> UserProfile:
    profile = db.session.query(UserProfile).filter_by(user_id=user_id).first()
    
    skills_json = json.dumps(skills) if skills else None
    
    if profile:
        profile.skills_json = skills_json
        profile.target_role = target_role
        if experience_years is not None:
            profile.experience_years = experience_years
        if experience_level is not None:
            profile.experience_level = experience_level
        if preferred_difficulty is not None:
            profile.preferred_difficulty = preferred_difficulty
    else:
        profile = UserProfile(
            user_id=user_id,
            skills_json=skills_json,
            target_role=target_role,
            experience_years=experience_years,
            experience_level=experience_level
        )
        db.session.add(profile)
        
    db.session.commit()
    db.session.refresh(profile)
    return profile

def get_user_profile(user_id: int) -> UserProfile | None:
    return db.session.query(UserProfile).filter_by(user_id=user_id).first()

def suggest_roles(user_id: int) -> list[dict]:
    profile = get_user_profile(user_id)
    if not profile or not profile.skills_json:
        return []
        
    try:
        skills_dict = json.loads(profile.skills_json)
    except Exception:
        return []
        
    # Flatten all detected skills into a lowercase set for matching
    user_skills_flat = set()
    for category_skills in skills_dict.values():
        for skill in category_skills:
            user_skills_flat.add(skill.lower())
            
    if not user_skills_flat:
        return []

    suggestions = []
    
    for role, keywords in ROLE_KEYWORDS.items():
        overlap = sum(1 for kw in keywords if kw.lower() in user_skills_flat)
        # Calculate a rough percentage match score
        match_score = int((overlap / len(keywords)) * 100) if keywords else 0
        suggestions.append({
            "role": role,
            "match_score": match_score
        })
        
    # Sort descending by match score
    suggestions.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Return top 3 non-zero suggestions
    return [s for s in suggestions if s["match_score"] > 0][:3]
