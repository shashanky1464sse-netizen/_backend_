from flask import Blueprint, request, jsonify, abort, send_from_directory
from app.schemas.user_profile import UserProfileSchema, UserProfileUpdateSchema
from app.services import user_profile_service
from app.core.security import get_current_user
from app.database import db
import os, uuid, json
from app.services.llm_service import validate_job_role, validate_skills

bp = Blueprint('profile', __name__)

profile_schema = UserProfileSchema()
profile_update_schema = UserProfileUpdateSchema()

@bp.route("/me", methods=["GET"])
def get_my_profile():
    """Return the current user's profile."""
    current_user = get_current_user()
    profile = user_profile_service.get_user_profile(current_user.id)
    
    if not profile:
        # If no profile exists yet, return an empty profile shell
        # to match Android DTO assumptions
        return jsonify({
            "id": 0,
            "user_id": current_user.id,
            "email": current_user.email,
            "name": None,
            "title": None,
            "location": None,
            "bio": None,
            "profile_photo_url": None,
            "skills_json": None,
            "previous_role": None,
            "target_role": None,
            "experience_level": None,
            "experience_years": None,
            "preferred_difficulty": "beginner",
            "updated_at": None,
        }), 200

    return jsonify(profile_schema.dump(profile)), 200


@bp.route("/me", methods=["PUT"])
def update_my_profile():
    """Update profile fields for the current user."""
    current_user = get_current_user()
    json_data = request.get_json()
    
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
        
    errors = profile_update_schema.validate(json_data)
    if errors:
        return jsonify(errors), 422
        
    # User Profile Service only has basic update currently, let's update fields directly
    profile = user_profile_service.get_user_profile(current_user.id)
    
    from app.models.user_profile import UserProfile
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        
    # Update User account email if changed
    if 'email' in json_data and json_data['email'] and json_data['email'] != current_user.email:
        # Avoid constraint violation if email already taken
        from app.models.user import User
        existing_user = User.query.filter_by(email=json_data['email']).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({"message": "Email already in use"}), 400
        current_user.email = json_data['email']
        db.session.add(current_user)

    if 'name' in json_data:
        profile.full_name = json_data['name']
    if 'title' in json_data:
        profile.job_title = json_data['title']
    if 'location' in json_data:
        profile.location = json_data['location']
    if 'bio' in json_data:
        profile.bio = json_data['bio']
    if 'profile_photo_url' in json_data:
        profile.profile_photo_url = json_data['profile_photo_url']
        
    if 'skills_json' in json_data:
        new_skills_str = json_data['skills_json']
        if new_skills_str and new_skills_str != profile.skills_json:
            try:
                new_skills_dict = json.loads(new_skills_str) if isinstance(new_skills_str, str) else new_skills_str
                old_skills_dict = {}
                if profile.skills_json:
                    try:
                        old_skills_dict = json.loads(profile.skills_json) if isinstance(profile.skills_json, str) else profile.skills_json
                    except json.JSONDecodeError:
                        pass
                
                old_skills_set = set()
                if isinstance(old_skills_dict, dict):
                    for v in old_skills_dict.values():
                        if isinstance(v, list):
                            old_skills_set.update(str(s).strip().lower() for s in v)
                
                if isinstance(new_skills_dict, dict):
                    for cat, v in new_skills_dict.items():
                        if isinstance(v, list):
                            added = [str(s).strip() for s in v if str(s).strip().lower() not in old_skills_set]
                            if added:
                                if not validate_skills(added):
                                    if cat == 'tools_frameworks':
                                        return jsonify({"message": "Invalid tools&framework"}), 422
                                    elif cat == 'soft_skills':
                                        return jsonify({"message": "Invalid soft skill"}), 422
                                    else:
                                        return jsonify({"message": "Invalid skill"}), 422
            except Exception:
                pass
        profile.skills_json = new_skills_str
        
    if 'target_role' in json_data:
        role = json_data['target_role']
        if role and role.strip() and role != profile.target_role:
            if not validate_job_role(role):
                return jsonify({"message": "Invalid role"}), 422
        profile.target_role = role
        
    if 'previous_role' in json_data:
        profile.previous_role = json_data['previous_role']
    if 'experience_level' in json_data:
        profile.experience_level = json_data['experience_level']
        
    if 'experience_years' in json_data:
        years = json_data['experience_years']
        if years is not None:
            try:
                y = int(years)
                if y < 0 or y > 50:
                    return jsonify({"message": "Invalid"}), 422
                profile.experience_years = y
            except (ValueError, TypeError):
                return jsonify({"message": "Invalid"}), 422
        else:
            profile.experience_years = None
            
    if 'preferred_difficulty' in json_data:
        profile.preferred_difficulty = json_data['preferred_difficulty']

    db.session.commit()
    db.session.refresh(profile)
    
    return jsonify(profile_schema.dump(profile)), 200


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'uploads')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/photo", methods=["POST"])
def upload_profile_photo():
    """Upload a profile photo for the current user."""
    current_user = get_current_user()

    if 'photo' not in request.files:
        return jsonify({"message": "No photo file provided"}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "File type not allowed"}), 400

    # Save file with a unique name to avoid collisions
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"profile_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    # Determine server base URL for full path
    photo_url = f"/uploads/{filename}"

    # Persist photo URL into user_profiles
    from app.models.user_profile import UserProfile
    profile = user_profile_service.get_user_profile(current_user.id)
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
    profile.profile_photo_url = photo_url
    db.session.commit()
    db.session.refresh(profile)

    return jsonify({"profile_photo_url": photo_url}), 200
