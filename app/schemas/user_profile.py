from marshmallow import Schema, fields, validate, EXCLUDE

class UserProfileSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    email = fields.Method("get_user_email", dump_only=True)
    name = fields.Str(attribute="full_name", allow_none=True)
    title = fields.Str(attribute="job_title", allow_none=True)
    location = fields.Str(allow_none=True)
    bio = fields.Str(allow_none=True)
    profile_photo_url = fields.Str(allow_none=True)
    skills_json = fields.Str(allow_none=True)
    target_role = fields.Str(allow_none=True)
    previous_role = fields.Str(allow_none=True)
    experience_years = fields.Int(allow_none=True)
    experience_level = fields.Str(allow_none=True)
    preferred_difficulty = fields.Str(allow_none=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

class UserProfileUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        
    name = fields.Str(allow_none=True)
    email = fields.Str(allow_none=True) # Accepting it but we might ignore/update User separately
    title = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    bio = fields.Str(allow_none=True)
    profile_photo_url = fields.Str(allow_none=True)
    skills_json = fields.Str(allow_none=True)
    target_role = fields.Str(allow_none=True)
    previous_role = fields.Str(allow_none=True)
    experience_years = fields.Int(allow_none=True)
    experience_level = fields.Str(allow_none=True)
    preferred_difficulty = fields.Str(allow_none=True)
