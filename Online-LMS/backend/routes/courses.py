"""
routes/courses.py
Course CRUD + search/filter, and lesson material uploads.
"""
import os
from flask import Blueprint, request

from config import config
from models.course_model import CourseModel
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.validator import require_fields, is_allowed_file, sanitize_string
from utils.helper import generate_unique_filename, ensure_dir
from utils.response import success_response, error_response

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/courses", methods=["GET"])
def get_courses():
    """GET /api/courses — public: list/search/filter published courses."""
    search = request.args.get("search")
    category = request.args.get("category")
    courses = CourseModel.get_all(search=search, category=category)
    return success_response("Courses fetched", courses)


@courses_bp.route("/courses/<int:course_id>", methods=["GET"])
def get_course_details(course_id):
    """GET /api/courses/<id> — public: course detail with its lessons."""
    course = CourseModel.get_by_id(course_id)
    if not course:
        return error_response("Course not found", 404)
    course["lessons"] = CourseModel.get_lessons(course_id)
    return success_response("Course fetched", course)


@courses_bp.route("/courses", methods=["POST"])
@token_required
@role_required("instructor", "admin")
def create_course():
    """POST /api/courses — instructor/admin: create a new course (with optional thumbnail)."""
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form
    else:
        data = request.get_json(silent=True) or {}

    errors = require_fields(data, ["title", "description"])
    if errors:
        return error_response("Validation failed", 422, errors)

    thumbnail_filename = None
    file = request.files.get("thumbnail") if request.files else None
    if file and file.filename:
        if not is_allowed_file(file.filename, config.ALLOWED_IMAGE_EXTENSIONS):
            return error_response("Invalid thumbnail image format", 422)
        ensure_dir(config.COURSE_UPLOAD_FOLDER)
        thumbnail_filename = generate_unique_filename(file.filename)
        file.save(os.path.join(config.COURSE_UPLOAD_FOLDER, thumbnail_filename))

    course_id = CourseModel.create(
        title=sanitize_string(data.get("title")),
        description=sanitize_string(data.get("description")),
        category=sanitize_string(data.get("category", "")),
        thumbnail=thumbnail_filename,
        price=data.get("price", 0) or 0,
        instructor_id=request.user["user_id"],
    )
    return success_response("Course created", {"id": course_id}, 201)


@courses_bp.route("/courses/<int:course_id>", methods=["PUT"])
@token_required
@role_required("instructor", "admin")
def update_course(course_id):
    """PUT /api/courses/<id> — instructor (owner) / admin: update course details."""
    course = CourseModel.get_by_id(course_id)
    if not course:
        return error_response("Course not found", 404)

    if request.user["role"] == "instructor" and course["instructor_id"] != request.user["user_id"]:
        return error_response("You can only edit your own courses", 403)

    data = request.get_json(silent=True) or {}
    CourseModel.update(
        course_id,
        title=sanitize_string(data.get("title", course["title"])),
        description=sanitize_string(data.get("description", course["description"])),
        category=sanitize_string(data.get("category", course["category"])),
        price=data.get("price", course["price"]),
        status=data.get("status", course["status"]),
    )
    return success_response("Course updated")


@courses_bp.route("/courses/<int:course_id>", methods=["DELETE"])
@token_required
@role_required("instructor", "admin")
def delete_course(course_id):
    """DELETE /api/courses/<id> — instructor (owner) / admin: delete a course."""
    course = CourseModel.get_by_id(course_id)
    if not course:
        return error_response("Course not found", 404)

    if request.user["role"] == "instructor" and course["instructor_id"] != request.user["user_id"]:
        return error_response("You can only delete your own courses", 403)

    CourseModel.delete(course_id)
    return success_response("Course deleted")


@courses_bp.route("/courses/<int:course_id>/lessons", methods=["POST"])
@token_required
@role_required("instructor", "admin")
def add_lesson(course_id):
    """
    POST /api/courses/<id>/lessons — instructor: add a module/lesson.

    Supports three lesson types:
      - 'video'   : an uploaded video file (mp4, mov, avi, mkv, webm)
      - 'youtube' : a YouTube video URL (no file upload; stored as a link)
      - 'pdf'     : an uploaded document (pdf, doc, docx, ppt, pptx, txt, zip)
    """
    course = CourseModel.get_by_id(course_id)
    if not course:
        return error_response("Course not found", 404)

    if request.user["role"] == "instructor" and course["instructor_id"] != request.user["user_id"]:
        return error_response("You can only edit your own courses", 403)

    title = sanitize_string(request.form.get("title"))
    lesson_type = request.form.get("type", "video")
    duration_min = request.form.get("duration_min", 0)
    position = request.form.get("position", 0)

    if not title:
        return error_response("Lesson title is required", 422)

    if lesson_type not in ("video", "youtube", "pdf", "link"):
        return error_response("Invalid lesson type", 422)

    file_path = None

    if lesson_type == "youtube":
        video_url = sanitize_string(request.form.get("video_url", ""))
        if not video_url:
            return error_response("A YouTube URL is required for this lesson type", 422)
        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            return error_response("Please provide a valid YouTube URL", 422)
        file_path = video_url

    elif lesson_type == "link":
        video_url = sanitize_string(request.form.get("video_url", ""))
        if not video_url:
            return error_response("A URL is required for this lesson type", 422)
        file_path = video_url

    else:
        file = request.files.get("file")
        if file and file.filename:
            allowed = (
                config.ALLOWED_VIDEO_EXTENSIONS
                if lesson_type == "video"
                else config.ALLOWED_DOCUMENT_EXTENSIONS
            )
            if not is_allowed_file(file.filename, allowed):
                return error_response("Invalid file type for this lesson type", 422)
            ensure_dir(config.COURSE_UPLOAD_FOLDER)
            filename = generate_unique_filename(file.filename)
            file.save(os.path.join(config.COURSE_UPLOAD_FOLDER, filename))
            file_path = filename
        else:
            return error_response("A file is required for this lesson type", 422)

    lesson_id = CourseModel.add_lesson(
        course_id, title, lesson_type, file_path, duration_min, position
    )
    return success_response("Lesson added", {"id": lesson_id}, 201)


@courses_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>", methods=["DELETE"])
@token_required
@role_required("instructor", "admin")
def delete_lesson(course_id, lesson_id):
    """DELETE /api/courses/<id>/lessons/<lesson_id> — instructor (owner) / admin: remove a module."""
    course = CourseModel.get_by_id(course_id)
    if not course:
        return error_response("Course not found", 404)

    if request.user["role"] == "instructor" and course["instructor_id"] != request.user["user_id"]:
        return error_response("You can only edit your own courses", 403)

    deleted = CourseModel.delete_lesson(lesson_id, course_id)
    if not deleted:
        return error_response("Lesson not found", 404)

    return success_response("Lesson deleted")


@courses_bp.route("/courses/<int:course_id>/lessons", methods=["GET"])
@token_required
def get_lessons(course_id):
    """GET /api/courses/<id>/lessons — enrolled student / instructor / admin view."""
    lessons = CourseModel.get_lessons(course_id)
    return success_response("Lessons fetched", lessons)


@courses_bp.route("/instructor/courses", methods=["GET"])
@token_required
@role_required("instructor", "admin")
def get_my_courses():
    """GET /api/instructor/courses — courses created by the logged-in instructor."""
    courses = CourseModel.get_by_instructor(request.user["user_id"])
    return success_response("Courses fetched", courses)
