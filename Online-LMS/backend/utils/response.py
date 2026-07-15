"""
response.py
Standard JSON response envelope used across all API endpoints.
"""
from flask import jsonify


def success_response(message="Success", data=None, status_code=200):
    """Uniform success envelope: { success, message, data }"""
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error_response(message="Something went wrong", status_code=400, errors=None):
    """Uniform error envelope: { success, message, errors }"""
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return jsonify(payload), status_code
