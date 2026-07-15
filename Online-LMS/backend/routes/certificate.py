"""
routes/certificate.py
Certificate generation and retrieval, gated on 100% course completion.
"""
from datetime import date
from flask import Blueprint, request

from database.database import execute_query
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.helper import generate_certificate_number
from utils.response import success_response, error_response

certificate_bp = Blueprint("certificate", __name__)


@certificate_bp.route("/certificate/<int:course_id>", methods=["POST"])
@token_required
@role_required("student")
def generate_certificate(course_id):
    """POST /api/certificate/<course_id> — generate a certificate once a course is fully completed."""
    student_id = request.user["user_id"]

    total_query = "SELECT COUNT(*) AS total FROM lessons WHERE course_id = %s"
    total_lessons = execute_query(total_query, (course_id,), fetch_one=True)["total"]

    done_query = """
        SELECT COUNT(*) AS done FROM progress
        WHERE course_id = %s AND student_id = %s AND is_completed = 1
    """
    completed = execute_query(done_query, (course_id, student_id), fetch_one=True)["done"]

    if total_lessons == 0 or completed < total_lessons:
        return error_response("Course must be 100% completed to generate a certificate", 400)

    existing_query = "SELECT * FROM certificates WHERE student_id = %s AND course_id = %s"
    existing = execute_query(existing_query, (student_id, course_id), fetch_one=True)
    if existing:
        return success_response("Certificate already generated", existing)

    cert_no = generate_certificate_number(student_id, course_id)
    insert_query = """
        INSERT INTO certificates (student_id, course_id, certificate_no, date)
        VALUES (%s, %s, %s, %s)
    """
    cert_id = execute_query(
        insert_query, (student_id, course_id, cert_no, date.today()), commit=True
    )

    return success_response(
        "Certificate generated",
        {"id": cert_id, "certificate_no": cert_no, "date": str(date.today())},
        201,
    )


@certificate_bp.route("/certificate/<int:course_id>", methods=["GET"])
@token_required
@role_required("student")
def get_certificate(course_id):
    """GET /api/certificate/<course_id> — fetch an existing certificate for the student."""
    query = """
        SELECT cert.*, u.name AS student_name, c.title AS course_title
        FROM certificates cert
        JOIN users u ON u.id = cert.student_id
        JOIN courses c ON c.id = cert.course_id
        WHERE cert.course_id = %s AND cert.student_id = %s
    """
    certificate = execute_query(
        query, (course_id, request.user["user_id"]), fetch_one=True
    )
    if not certificate:
        return error_response("Certificate not found. Complete the course first.", 404)

    return success_response("Certificate fetched", certificate)
