"""
helper.py
General-purpose helpers: password hashing, JWT encode/decode, unique filenames,
and certificate number generation.
"""
import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from config import config


# ---------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------
def generate_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXP_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str):
    """Returns the decoded payload dict, or raises jwt exceptions on failure."""
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


# ---------------------------------------------------------------------
# File naming
# ---------------------------------------------------------------------
def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""
    unique_name = f"{uuid.uuid4().hex}"
    return f"{unique_name}.{ext}" if ext else unique_name


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------
# Certificate numbers
# ---------------------------------------------------------------------
def generate_certificate_number(student_id: int, course_id: int) -> str:
    stamp = datetime.now().strftime("%Y%m%d")
    return f"RRLMS-{course_id:04d}-{student_id:04d}-{stamp}"
