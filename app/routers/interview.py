from flask import Blueprint, request, jsonify, abort

from app.schemas.interview import InterviewCreateSchema, InterviewSchema, InterviewListSchema
from app.services import interview_service
from app.core.security import get_current_user

bp = Blueprint('interview', __name__)

interview_create_schema = InterviewCreateSchema()
interview_schema = InterviewSchema()
interviews_list_schema = InterviewListSchema(many=True)

@bp.route("/", methods=["POST"])
def create_interview():
    """
    Accept a list of question/answer/category triples, score them,
    determine feedback level, and persist the interview record.
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    # Validate and deserialize input
    errors = interview_create_schema.validate(json_data)
    if errors:
        return jsonify(errors), 422
    
    current_user = get_current_user()
    interview = interview_service.create_interview(json_data, current_user.id)
    return jsonify(interview_schema.dump(interview)), 201


@bp.route("/", methods=["GET"])
def list_interviews():
    """Return all interviews for current user, newest first, with skills only (no Q&A for perf)."""
    current_user = get_current_user()
    interviews = interview_service.get_all_interviews(current_user.id)
    return jsonify(interviews_list_schema.dump(interviews))


@bp.route("/<int:interview_id>", methods=["GET"])
def get_interview(interview_id):
    """Return a single interview by ID for current user, or 404 if not found."""
    current_user = get_current_user()
    interview = interview_service.get_interview_by_id(interview_id, current_user.id)
    if interview is None:
        abort(404, description=f"Interview {interview_id} not found")
    return jsonify(interview_schema.dump(interview))
