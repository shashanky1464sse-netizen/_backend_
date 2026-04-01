from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.core.config import get_settings
from app.database import db
from app.core.errors import register_error_handlers

# Import blueprints
from app.routers.health import bp as health_bp
from app.routers.interview import bp as interview_bp
from app.routers.resume import bp as resume_bp
from app.routers.auth import bp as auth_bp
from app.routers.analytics import bp as analytics_bp
from app.routers.roles import bp as roles_bp
from app.routers.user_profile import bp as profile_bp

settings = get_settings()

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = settings.secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Rate Limiting (200 requests per minute by default globally)
    # Exclude static files if needed, but for an API this is solid protection.
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri="memory://" # Can swap to redis:// in larger horizontally scaled deploys
    )

    # Exception Handling - Catch all unexpected errors and HTTP errors to JSON format
    register_error_handlers(app)

    # Initialize extensions
    db.init_app(app)

    # Database migrations will be handled by Alembic instead of create_all()
    with app.app_context():
        from app import models

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(interview_bp, url_prefix="/interviews")
    app.register_blueprint(resume_bp, url_prefix="/resume")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(roles_bp, url_prefix="/roles")
    app.register_blueprint(profile_bp, url_prefix="/profile")

    # Serve uploaded profile photos statically
    import os
    from flask import send_from_directory
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(uploads_dir, filename)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=settings.debug, host="0.0.0.0", port=5000, use_reloader=False)

