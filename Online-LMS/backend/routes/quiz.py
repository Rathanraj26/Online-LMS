"""
routes/quiz.py
Quiz creation, question management, and answer submission/scoring.
"""
from flask import Blueprint, request

from models.quiz_model import QuizModel
from middleware.auth_middleware import token_required
from middleware.role_middleware import role_required
from utils.validator import require_fields, sanitize_string
from utils.response import success_response, error_response

quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.route("/quizzes", methods=["GET"])
@token_required
def get_quizzes():
    """GET /api/quizzes?course_id=<id> — list quizzes for a course."""
    course_id = request.args.get("course_id")
    if not course_id:
        return error_response("'course_id' query param is required", 422)
    quizzes = QuizModel.get_by_course(course_id)
    return success_response("Quizzes fetched", quizzes)


@quiz_bp.route("/quizzes/<int:quiz_id>/questions", methods=["GET"])
@token_required
def get_quiz_questions(quiz_id):
    """GET /api/quizzes/<id>/questions — fetch questions WITHOUT correct answers (for taking the quiz)."""
    questions = QuizModel.get_questions(quiz_id, include_answer=False)
    return success_response("Questions fetched", questions)


@quiz_bp.route("/quizzes", methods=["POST"])
@token_required
@role_required("instructor", "admin")
def create_quiz():
    """POST /api/quizzes — instructor: create a quiz, optionally with an initial question list."""
    data = request.get_json(silent=True) or {}
    errors = require_fields(data, ["course_id", "title"])
    if errors:
        return error_response("Validation failed", 422, errors)

    quiz_id = QuizModel.create(
        data["course_id"], sanitize_string(data["title"]), data.get("duration_min", 10)
    )

    for q in data.get("questions", []):
        q_errors = require_fields(q, ["question", "options", "answer"])
        if q_errors:
            continue
        QuizModel.add_question(quiz_id, q["question"], q["options"], q["answer"])

    return success_response("Quiz created", {"id": quiz_id}, 201)


@quiz_bp.route("/quizzes/<int:quiz_id>/questions", methods=["POST"])
@token_required
@role_required("instructor", "admin")
def add_question(quiz_id):
    """POST /api/quizzes/<id>/questions — instructor: add a single question to a quiz."""
    data = request.get_json(silent=True) or {}
    errors = require_fields(data, ["question", "options", "answer"])
    if errors:
        return error_response("Validation failed", 422, errors)

    question_id = QuizModel.add_question(quiz_id, data["question"], data["options"], data["answer"])
    return success_response("Question added", {"id": question_id}, 201)


@quiz_bp.route("/results", methods=["POST"])
@token_required
@role_required("student")
def submit_quiz():
    """
    POST /api/results — student: submit answers for a quiz; server grades and stores the result.
    Body: { "quiz_id": 1, "answers": { "<question_id>": "<selected option>", ... } }
    """
    data = request.get_json(silent=True) or {}
    errors = require_fields(data, ["quiz_id", "answers"])
    if errors:
        return error_response("Validation failed", 422, errors)

    quiz_id = data["quiz_id"]
    submitted_answers = data["answers"]

    questions = QuizModel.get_questions(quiz_id, include_answer=True)
    total = len(questions)
    score = 0
    for q in questions:
        selected = submitted_answers.get(str(q["id"]))
        if selected is not None and str(selected).strip() == str(q["answer"]).strip():
            score += 1

    QuizModel.save_result(request.user["user_id"], quiz_id, score, total)
    return success_response("Quiz submitted", {"score": score, "total": total}, 201)


@quiz_bp.route("/results", methods=["GET"])
@token_required
@role_required("student")
def get_results():
    """GET /api/results — student: view all of their own quiz results."""
    results = QuizModel.get_results_for_student(request.user["user_id"])
    return success_response("Results fetched", results)
