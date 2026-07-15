"""
routes/assignments.py
Assignment creation, submission, and grading.
"""
import os
from flask import Blueprint, request

from config import config
from models.assignment_model import AssignmentModel
from models.course_model import CourseModel
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.validator import require_fields, is_allowed_file, sanitize_string
from utils.helper import generate_unique_filename, ensure_dir
from utils.response import success_response, error_response

assignments_bp = Blueprint("assignments", __name__)


@assignments_bp.route("/assignments", methods=["GET"])
@token_required
def get_assignments():
    """GET /api/assignments?course_id=<id> — list assignments for a course."""
    course_id = request.args.get("course_id")
    if not course_id:
        return error_response("'course_id' query param is required", 422)
    assignments = AssignmentModel.get_by_course(course_id)
    return success_response("Assignments fetched", assignments)


@assignments_bp.route("/assignments", methods=["POST"])
@token_required
@role_required("instructor", "admin")
def create_assignment():
    """POST /api/assignments — instructor: create an assignment for a course."""
    data = request.get_json(silent=True) or {}
    errors = require_fields(data, ["course_id", "title", "deadline"])
    if errors:
        return error_response("Validation failed", 422, errors)

    course = CourseModel.get_by_id(data["course_id"])
    if not course:
        return error_response("Course not found", 404)

    assignment_id = AssignmentModel.create(
        course_id=data["course_id"],
        title=sanitize_string(data["title"]),
        description=sanitize_string(data.get("description", "")),
        deadline=data["deadline"],
        max_marks=data.get("max_marks", 100),
    )
    return success_response("Assignment created", {"id": assignment_id}, 201)


@assignments_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"])
@token_required
@role_required("instructor", "admin")
def delete_assignment(assignment_id):
    """DELETE /api/assignments/<id> — instructor/admin: remove an assignment."""
    AssignmentModel.delete(assignment_id)
    return success_response("Assignment deleted")


@assignments_bp.route("/submissions", methods=["POST"])
@token_required
@role_required("student")
def submit_assignment():
    """POST /api/submissions — student: upload a file for an assignment."""
    assignment_id = request.form.get("assignment_id")
    if not assignment_id:
        return error_response("'assignment_id' is required", 422)

    assignment = AssignmentModel.get_by_id(assignment_id)
    if not assignment:
        return error_response("Assignment not found", 404)

    file = request.files.get("file")
    if not file or not file.filename:
        return error_response("A file is required for submission", 422)

    if not is_allowed_file(file.filename, config.ALLOWED_DOCUMENT_EXTENSIONS):
        return error_response("Invalid file type", 422)

    ensure_dir(config.ASSIGNMENT_UPLOAD_FOLDER)
    filename = generate_unique_filename(file.filename)
    file.save(os.path.join(config.ASSIGNMENT_UPLOAD_FOLDER, filename))

    AssignmentModel.submit(assignment_id, request.user["user_id"], filename)
    return success_response("Assignment submitted successfully", status_code=201)


@assignments_bp.route("/assignments/<int:assignment_id>/submissions", methods=["GET"])
@token_required
@role_required("instructor", "admin")
def list_submissions(assignment_id):
    """GET /api/assignments/<id>/submissions — instructor: review all submissions."""
    submissions = AssignmentModel.get_submissions_for_assignment(assignment_id)
    return success_response("Submissions fetched", submissions)


@assignments_bp.route("/submissions/<int:submission_id>/grade", methods=["PUT"])
@token_required
@role_required("instructor", "admin")
def grade_submission(submission_id):
    """PUT /api/submissions/<id>/grade — instructor: assign marks + feedback."""
    data = request.get_json(silent=True) or {}
    errors = require_fields(data, ["marks_obtained"])
    if errors:
        return error_response("Validation failed", 422, errors)

    AssignmentModel.grade(
        submission_id, data["marks_obtained"], sanitize_string(data.get("feedback", ""))
    )
    return success_response("Submission graded")
