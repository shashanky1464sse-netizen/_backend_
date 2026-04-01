"""
schemas/resume.py
~~~~~~~~~~~~~~~~~
Marshmallow request/response models for the /resume/ router.

IMPORTANT: Use load_default/dump_default (callable) — NOT missing=list.
           In Marshmallow 3.x, passing the builtin `list` as missing= causes
           TypeError: 'builtin_function_or_method' not iterable on dump().
"""

from marshmallow import Schema, fields, EXCLUDE


def _list():
    return []


def _dict():
    return {}


class TechnicalSkillsSchema(Schema):
    """Categorised technical skills detected in the resume."""
    class Meta:
        unknown = EXCLUDE          # silently ignore extra subcategories

    languages    = fields.List(fields.String(), load_default=_list, dump_default=_list)
    backend      = fields.List(fields.String(), load_default=_list, dump_default=_list)
    frontend     = fields.List(fields.String(), load_default=_list, dump_default=_list)
    mobile       = fields.List(fields.String(), load_default=_list, dump_default=_list)
    database     = fields.List(fields.String(), load_default=_list, dump_default=_list)
    devops       = fields.List(fields.String(), load_default=_list, dump_default=_list)
    ai           = fields.List(fields.String(), load_default=_list, dump_default=_list)
    architecture = fields.List(fields.String(), load_default=_list, dump_default=_list)
    testing      = fields.List(fields.String(), load_default=_list, dump_default=_list)


class AiClassifiedSkillsSchema(Schema):
    """Skills the AI Layer-7 fallback classified from unknown candidates."""
    class Meta:
        unknown = EXCLUDE

    technical_skills = fields.List(fields.String(), load_default=_list, dump_default=_list)
    tools_frameworks = fields.List(fields.String(), load_default=_list, dump_default=_list)
    soft_skills      = fields.List(fields.String(), load_default=_list, dump_default=_list)


class InterviewQuestionSchema(Schema):
    """A single generated interview question."""
    question = fields.String(required=True)
    category = fields.String(required=True)
    type     = fields.String(required=True)


class ResumeAnalysisOutSchema(Schema):
    """Full response returned by POST /resume/upload."""
    class Meta:
        unknown = EXCLUDE

    technical_skills          = fields.Nested(TechnicalSkillsSchema, required=True)
    tools_frameworks          = fields.List(fields.String(), load_default=_list, dump_default=_list)
    soft_skills               = fields.List(fields.String(), load_default=_list, dump_default=_list)
    unknown_skills            = fields.List(fields.String(), load_default=_list, dump_default=_list)
    # ai_classified_skills is sent to the web frontend so it can augment the skill display
    ai_classified_skills      = fields.Nested(AiClassifiedSkillsSchema, load_default=_dict, dump_default=_dict)
    detected_experience_years = fields.Integer(load_default=0, dump_default=0)
    inferred_target_role      = fields.String(load_default=None, dump_default=None, allow_none=True)
    experience_level          = fields.String(load_default="Beginner", dump_default="Beginner")
    generated_questions       = fields.List(
        fields.Nested(InterviewQuestionSchema),
        load_default=_list,
        dump_default=_list,
    )


class GenerateQuestionsRequestSchema(Schema):
    """Request payload for POST /resume/generate-questions."""
    skills           = fields.List(fields.String(), required=True)
    soft_skills      = fields.List(fields.String(), load_default=_list)
    tools_frameworks = fields.List(fields.String(), load_default=_list)
    target_role      = fields.String(required=False, allow_none=True, load_default=None)
    experience_years = fields.Integer(required=False, allow_none=True, load_default=None)
    difficulty       = fields.String(required=False, allow_none=True, load_default=None)


class GenerateQuestionsResponseSchema(Schema):
    """Response payload for POST /resume/generate-questions."""
    generated_questions = fields.List(fields.Nested(InterviewQuestionSchema), required=True)
