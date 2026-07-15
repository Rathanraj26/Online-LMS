"""
routes/users.py
User management (admin) and profile endpoints.
"""
import os
from flask import Blueprint, request

from config import config
from models.user_model import UserModel
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.validator import is_allowed_file, sanitize_string
from utils.helper import generate_unique_filename, ensure_dir
from utils.response import success_response, error_response

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
@token_required
@role_required("admin")
def get_users():
    """GET /api/users — admin: list all users (optional ?role=student filter)."""
    role = request.args.get("role")
    users = UserModel.get_all(role)
    return success_response("Users fetched", users)


@users_bp.route("/users/<int:user_id>/status", methods=["PUT"])
@token_required
@role_required("admin")
def toggle_user_status(user_id):
    """PUT /api/users/<id>/status — admin: activate/deactivate a user account."""
    data = request.get_json(silent=True) or {}
    is_active = bool(data.get("is_active", True))
    UserModel.set_active_status(user_id, is_active)
    return success_response("User status updated")


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@role_required("admin")
def delete_user(user_id):
    """DELETE /api/users/<id> — admin: remove a user account."""
    UserModel.delete(user_id)
    return success_response("User deleted")


@users_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """GET /api/profile — current logged-in user's profile."""
    user = UserModel.find_by_id(request.user["user_id"])
    if not user:
        return error_response("User not found", 404)
    return success_response("Profile fetched", user)


@users_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """PUT /api/profile — update name / phone / bio / avatar for the logged-in user."""
    user_id = request.user["user_id"]

    # multipart/form-data (with optional avatar file) or plain JSON
    if request.content_type and "multipart/form-data" in request.content_type:
        name = sanitize_string(request.form.get("name"))
        phone = sanitize_string(request.form.get("phone"))
        bio = sanitize_string(request.form.get("bio"))
        avatar_filename = None

        file = request.files.get("avatar")
        if file and file.filename:
            if not is_allowed_file(file.filename, config.ALLOWED_IMAGE_EXTENSIONS):
                return error_response("Invalid image format for avatar", 422)
            ensure_dir(config.PROFILE_UPLOAD_FOLDER)
            avatar_filename = generate_unique_filename(file.filename)
            file.save(os.path.join(config.PROFILE_UPLOAD_FOLDER, avatar_filename))

        UserModel.update_profile(user_id, name, phone, bio, avatar_filename)
    else:
        data = request.get_json(silent=True) or {}
        UserModel.update_profile(
            user_id,
            name=sanitize_string(data.get("name")),
            phone=sanitize_string(data.get("phone")),
            bio=sanitize_string(data.get("bio")),
        )

    updated_user = UserModel.find_by_id(user_id)
    return success_response("Profile updated", updated_user)
