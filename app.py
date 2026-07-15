"""
app.py
Application factory + entrypoint for the RR - Online Learning Management System API.
"""
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import config
from database.database import init_pool
from utils.response import error_response

# Blueprints
from routes.auth import auth_bp
from routes.users import users_bp
from routes.courses import courses_bp
from routes.enrollment import enrollment_bp
from routes.assignments import assignments_bp
from routes.quiz import quiz_bp
from routes.progress import progress_bp
from routes.certificate import certificate_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Allow the frontend (served separately) to call this API
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize the MySQL connection pool once at startup
    init_pool()

    # Register all API blueprints under /api
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(courses_bp, url_prefix="/api")
    app.register_blueprint(enrollment_bp, url_prefix="/api")
    app.register_blueprint(assignments_bp, url_prefix="/api")
    app.register_blueprint(quiz_bp, url_prefix="/api")
    app.register_blueprint(progress_bp, url_prefix="/api")
    app.register_blueprint(certificate_bp, url_prefix="/api")

    # Serve uploaded files (profile pics, course videos/pdfs, assignment submissions)
    @app.route("/uploads/<folder>/<filename>")
    def serve_upload(folder, filename):
        allowed_folders = {"profile", "courses", "assignments"}
        if folder not in allowed_folders:
            return error_response("Not found", 404)
        return send_from_directory(f"{config.UPLOAD_FOLDER}/{folder}", filename)

    @app.route("/api/health")
    def health_check():
        return {"success": True, "message": "RR-LMS API is running"}, 200

    # ---------------- Centralized error handlers ----------------
    @app.errorhandler(404)
    def not_found(e):
        return error_response("Resource not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("Method not allowed", 405)

    @app.errorhandler(413)
    def file_too_large(e):
        return error_response("Uploaded file is too large", 413)

    @app.errorhandler(500)
    def internal_error(e):
        return error_response("Internal server error", 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
