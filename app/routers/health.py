from flask import Blueprint, jsonify
from sqlalchemy import text
from app.database import db

bp = Blueprint('health', __name__)

@bp.route("/health", methods=["GET"])
def health_check():
    """Returns a simple running status — useful for load-balancer and Android app checks."""
    return jsonify({"status": "ok"})

@bp.route("/ready", methods=["GET"])
def ready_check():
    """Checks availability of dependencies like Database and LLM."""
    components = {
        "database": "unknown",
        "llm_service": "ok" # LLM is local dummy function so it's nominally always assumed ok
    }
    overall_status = "ok"

    # Database connection check
    try:
        db.session.execute(text('SELECT 1'))
        components["database"] = "ok"
    except Exception as e:
        components["database"] = f"error: {str(e)}"
        overall_status = "error"

    status_code = 200 if overall_status == "ok" else 503

    return jsonify({
        "status": overall_status,
        "components": components
    }), status_code

