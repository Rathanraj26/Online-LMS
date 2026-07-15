"""
routes/enrollment.py
Student course enrollment and access.
"""
from flask import Blueprint, request

from models.course_model import CourseModel
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.response import success_response, error_response

enrollment_bp = Blueprint("enrollment", __name__)


@enrollment_bp.route("/enroll", methods=["POST"])
@token_required
@role_required("student")
def enroll():
    """POST /api/enroll — student: enroll in a course."""
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")

    if not course_id:
        return error_response("'course_id' is required", 422)

    course = CourseModel.get_by_id(course_id)
    if not course:
        return error_response("Course not found", 404)

    if CourseModel.is_enrolled(request.user["user_id"], course_id):
        return error_response("You are already enrolled in this course", 409)

    CourseModel.enroll(request.user["user_id"], course_id)
    return success_response("Enrolled successfully", status_code=201)


@enrollment_bp.route("/my-courses", methods=["GET"])
@token_required
@role_required("student")
def my_courses():
    """GET /api/my-courses — student: list all enrolled courses."""
    courses = CourseModel.get_enrolled_courses(request.user["user_id"])
    return success_response("Enrolled courses fetched", courses)


@enrollment_bp.route("/courses/<int:course_id>/students", methods=["GET"])
@token_required
@role_required("instructor", "admin")
def enrolled_students(course_id):
    """GET /api/courses/<id>/students — instructor/admin: roster for a course."""
    students = CourseModel.get_enrolled_students(course_id)
    return success_response("Enrolled students fetched", students)
