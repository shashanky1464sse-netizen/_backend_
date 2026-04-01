from marshmallow import Schema, fields

class QuestionAnswerCreateSchema(Schema):
    question = fields.String(required=True)
    answer = fields.String(required=True)
    category = fields.String(required=True)

class QuestionAnswerSchema(Schema):
    id = fields.Integer(dump_only=True)
    question = fields.String(dump_only=True)
    answer = fields.String(dump_only=True)
    category = fields.String(dump_only=True)
    score = fields.Integer(dump_only=True)
    strengths = fields.String(dump_only=True)
    improvements = fields.String(dump_only=True)
    suggestions = fields.String(dump_only=True)

class SkillCreateSchema(Schema):
    skill_name = fields.String(required=True)

class SkillSchema(Schema):
    id = fields.Integer(dump_only=True)
    skill_name = fields.String(dump_only=True)
    category_score = fields.Integer(dump_only=True)

class InterviewCreateSchema(Schema):
    responses = fields.List(fields.Nested(QuestionAnswerCreateSchema), required=True)
    role_applied_for = fields.String(required=False, allow_none=True)

class InterviewSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    feedback_level = fields.String(dump_only=True)
    score = fields.Integer(dump_only=True)
    summary = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    role_applied_for = fields.String(dump_only=True)
    responses = fields.List(fields.Nested(QuestionAnswerSchema), dump_only=True, data_key="question_answers")
    skills = fields.List(fields.Nested(SkillSchema), dump_only=True)

# Lightweight schema for the list endpoint — skips per-Q&A data to avoid N+1 serialization
class InterviewListSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    feedback_level = fields.String(dump_only=True)
    score = fields.Integer(dump_only=True)
    summary = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    role_applied_for = fields.String(dump_only=True)
    skills = fields.List(fields.Nested(SkillSchema), dump_only=True)
