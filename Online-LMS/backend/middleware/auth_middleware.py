"""
auth_middleware.py
`@token_required` decorator: validates the JWT sent in the Authorization header
(Bearer scheme) and attaches the decoded user info to `request.user`.
"""
from functools import wraps
import jwt
from flask import request

from utils.helper import decode_token
from utils.response import error_response


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return error_response("Authorization token is missing", 401)

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error_response("Token has expired, please log in again", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid authentication token", 401)

        # Attach decoded identity to the request context for downstream use
        request.user = {"user_id": payload["user_id"], "role": payload["role"]}
        return f(*args, **kwargs)

    return decorated
