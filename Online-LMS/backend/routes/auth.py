"""
routes/auth.py
Authentication endpoints: register, login, logout.
"""
from flask import Blueprint, request

from models.user_model import UserModel
from utils.helper import hash_password, verify_password, generate_token
from utils.validator import is_valid_email, is_valid_password, require_fields, sanitize_string
from utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """POST /api/register — create a new user account."""
    data = request.get_json(silent=True) or {}

    errors = require_fields(data, ["name", "email", "password"])
    if errors:
        return error_response("Validation failed", 422, errors)

    name = sanitize_string(data.get("name"))
    email = sanitize_string(data.get("email")).lower()
    password = data.get("password")
    role = data.get("role", "student")

    if role not in ("student", "instructor"):
        # Admin accounts are provisioned manually / by another admin, not via public signup
        role = "student"

    if not is_valid_email(email):
        return error_response("Invalid email address", 422)

    if not is_valid_password(password):
        return error_response("Password must be at least 6 characters long", 422)

    if UserModel.find_by_email(email):
        return error_response("An account with this email already exists", 409)

    hashed = hash_password(password)
    user_id = UserModel.create(name, email, hashed, role)
    token = generate_token(user_id, role)

    return success_response(
        "Registration successful",
        {"token": token, "user": {"id": user_id, "name": name, "email": email, "role": role}},
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/login — authenticate and issue a JWT."""
    data = request.get_json(silent=True) or {}

    errors = require_fields(data, ["email", "password"])
    if errors:
        return error_response("Validation failed", 422, errors)

    email = sanitize_string(data.get("email")).lower()
    password = data.get("password")

    user = UserModel.find_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return error_response("Invalid email or password", 401)

    if not user["is_active"]:
        return error_response("This account has been deactivated", 403)

    token = generate_token(user["id"], user["role"])
    return success_response(
        "Login successful",
        {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
            },
        },
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """POST /api/logout — stateless JWT: the client simply discards the token."""
    return success_response("Logged out successfully")
