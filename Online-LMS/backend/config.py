"""
config.py
Central application configuration, loaded from environment variables (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base Flask configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 24))
    JWT_ALGORITHM = "HS256"

    # Database (MySQL)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "rr_lms")

    # Uploads
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    PROFILE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "profile")
    COURSE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "courses")
    ASSIGNMENT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "assignments")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 50 * 1024 * 1024))

    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "zip"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


config = Config()
