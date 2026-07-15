"""
quiz_model.py
Data-access layer for `quizzes`, `questions`, and `results`.
"""
import json
from database.database import execute_query


class QuizModel:

    # ---------------- Quizzes ----------------
    @staticmethod
    def create(course_id, title, duration_min):
        query = "INSERT INTO quizzes (course_id, title, duration_min) VALUES (%s, %s, %s)"
        return execute_query(query, (course_id, title, duration_min), commit=True)

    @staticmethod
    def get_by_course(course_id):
        query = "SELECT * FROM quizzes WHERE course_id = %s ORDER BY created_at DESC"
        return execute_query(query, (course_id,), fetch_all=True)

    @staticmethod
    def get_by_id(quiz_id):
        query = "SELECT * FROM quizzes WHERE id = %s"
        return execute_query(query, (quiz_id,), fetch_one=True)

    # ---------------- Questions ----------------
    @staticmethod
    def add_question(quiz_id, question, options: list, answer):
        query = """
            INSERT INTO questions (quiz_id, question, options, answer)
            VALUES (%s, %s, %s, %s)
        """
        return execute_query(
            query, (quiz_id, question, json.dumps(options), answer), commit=True
        )

    @staticmethod
    def get_questions(quiz_id, include_answer=False):
        if include_answer:
            query = "SELECT * FROM questions WHERE quiz_id = %s"
        else:
            query = "SELECT id, quiz_id, question, options FROM questions WHERE quiz_id = %s"
        rows = execute_query(query, (quiz_id,), fetch_all=True)
        for row in rows:
            if isinstance(row.get("options"), str):
                row["options"] = json.loads(row["options"])
        return rows

    # ---------------- Results ----------------
    @staticmethod
    def save_result(student_id, quiz_id, score, total):
        query = """
            INSERT INTO results (student_id, quiz_id, score, total)
            VALUES (%s, %s, %s, %s)
        """
        return execute_query(query, (student_id, quiz_id, score, total), commit=True)

    @staticmethod
    def get_results_for_student(student_id):
        query = """
            SELECT r.*, q.title AS quiz_title, c.title AS course_title
            FROM results r
            JOIN quizzes q ON q.id = r.quiz_id
            JOIN courses c ON c.id = q.course_id
            WHERE r.student_id = %s
            ORDER BY r.taken_at DESC
        """
        return execute_query(query, (student_id,), fetch_all=True)
