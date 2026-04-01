from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.core.logger import get_logger

logger = get_logger(__name__)

def register_error_handlers(app):
    """Registers standard JSON error handling for both expected HTTP errors and unexpected 500s."""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Standard werkzeug HTTP exceptions (404, 400, 429, etc)."""
        response = e.get_response()
        response.data = jsonify({
            "error": e.name,
            "message": e.description,
            "code": e.code
        }).data
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global catch-all for unexpected server errors (500)."""
        # Always log the full traceback server-side
        logger.exception("Unhandled exception occurred: %s", e)
        
        # In production, do not leak tracelog to user
        is_debug = app.config.get("DEBUG", False)
        
        error_msg = str(e) if is_debug else "An unexpected internal server error occurred."
        
        return jsonify({
            "error": "Internal Server Error",
            "message": error_msg,
            "code": 500
        }), 500
