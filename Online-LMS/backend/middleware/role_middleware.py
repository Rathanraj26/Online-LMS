"""
role_middleware.py
`@role_required(*roles)` decorator: restricts an endpoint to one or more roles.
Must be used AFTER `@token_required` so `request.user` is already populated.
"""
from functools import wraps
from flask import request
from utils.response import error_response


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, "user", None)
            if not user:
                return error_response("Authentication required", 401)

            if user["role"] not in allowed_roles:
                return error_response(
                    "You do not have permission to perform this action", 403
                )
            return f(*args, **kwargs)

        return decorated

    return decorator
