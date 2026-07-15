"""
routes/progress.py
Tracks per-lesson completion and overall course-completion percentage.
"""
from flask import Blueprint, request

from database.database import execute_query
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.validator import require_fields
from utils.response import success_response, error_response

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/progress/complete", methods=["POST"])
@token_required
@role_required("student")
def mark_lesson_complete():
    """POST /api/progress/complete — student: mark a lesson as watched/completed."""
    data = request.get_json(silent=True) or {}
    errors = require_fields(data, ["course_id", "lesson_id"])
    if errors:
        return error_response("Validation failed", 422, errors)

    query = """
        INSERT INTO progress (student_id, course_id, lesson_id, is_completed, completed_at)
        VALUES (%s, %s, %s, 1, NOW())
        ON DUPLICATE KEY UPDATE is_completed = 1, completed_at = NOW()
    """
    execute_query(
        query, (request.user["user_id"], data["course_id"], data["lesson_id"]), commit=True
    )
    return success_response("Progress updated")


@progress_bp.route("/progress/<int:course_id>", methods=["GET"])
@token_required
def get_course_progress(course_id):
    """GET /api/progress/<course_id> — completion percentage for the logged-in student."""
    student_id = request.user["user_id"]

    total_query = "SELECT COUNT(*) AS total FROM lessons WHERE course_id = %s"
    total_lessons = execute_query(total_query, (course_id,), fetch_one=True)["total"]

    done_query = """
        SELECT COUNT(*) AS done FROM progress
        WHERE course_id = %s AND student_id = %s AND is_completed = 1
    """
    completed = execute_query(done_query, (course_id, student_id), fetch_one=True)["done"]

    percentage = round((completed / total_lessons) * 100, 2) if total_lessons else 0

    return success_response(
        "Progress fetched",
        {"total_lessons": total_lessons, "completed": completed, "percentage": percentage},
    )
