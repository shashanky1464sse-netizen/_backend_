from flask import Blueprint, request, jsonify
from app.services import user_profile_service
from app.core.security import get_current_user

bp = Blueprint('roles', __name__)

@bp.route("/profile", methods=["POST"])
def update_profile():
    """
    Saves or updates the explicit UserProfile following a resume parse confirmation.
    Expected JSON: {
        "skills": {...structured tech skills...},
        "target_role": "..."
    }
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
        
    current_user = get_current_user()
    skills = json_data.get("skills", {})
    target = json_data.get("target_role")
    
    profile = user_profile_service.update_user_profile(current_user.id, skills, target)
    return jsonify({"message": "Profile updated", "target_role": profile.target_role}), 200


@bp.route("/suggest", methods=["GET"])
def suggest_roles():
    """
    Suggests roles based on the current user's profile skills.
    Returns: {"suggested_roles": [{"role": "Backend Engineer", "match_score": 80}]}
    """
    current_user = get_current_user()
    suggestions = user_profile_service.suggest_roles(current_user.id)
    return jsonify({"suggested_roles": suggestions}), 200
