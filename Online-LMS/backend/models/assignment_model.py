"""
assignment_model.py
Data-access layer for `assignments` and `submissions`.
"""
from database.database import execute_query


class AssignmentModel:

    # ---------------- Assignments ----------------
    @staticmethod
    def create(course_id, title, description, deadline, max_marks):
        query = """
            INSERT INTO assignments (course_id, title, description, deadline, max_marks)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(
            query, (course_id, title, description, deadline, max_marks), commit=True
        )

    @staticmethod
    def get_by_course(course_id):
        query = "SELECT * FROM assignments WHERE course_id = %s ORDER BY deadline ASC"
        return execute_query(query, (course_id,), fetch_all=True)

    @staticmethod
    def get_by_id(assignment_id):
        query = "SELECT * FROM assignments WHERE id = %s"
        return execute_query(query, (assignment_id,), fetch_one=True)

    @staticmethod
    def delete(assignment_id):
        query = "DELETE FROM assignments WHERE id = %s"
        return execute_query(query, (assignment_id,), commit=True)

    # ---------------- Submissions ----------------
    @staticmethod
    def submit(assignment_id, student_id, file_path):
        query = """
            INSERT INTO submissions (assignment_id, student_id, file)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE file = VALUES(file), status = 'submitted',
                                     submitted_at = CURRENT_TIMESTAMP, marks_obtained = NULL
        """
        return execute_query(query, (assignment_id, student_id, file_path), commit=True)

    @staticmethod
    def get_submissions_for_assignment(assignment_id):
        query = """
            SELECT s.*, u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN users u ON u.id = s.student_id
            WHERE s.assignment_id = %s
            ORDER BY s.submitted_at DESC
        """
        return execute_query(query, (assignment_id,), fetch_all=True)

    @staticmethod
    def get_student_submission(assignment_id, student_id):
        query = "SELECT * FROM submissions WHERE assignment_id = %s AND student_id = %s"
        return execute_query(query, (assignment_id, student_id), fetch_one=True)

    @staticmethod
    def grade(submission_id, marks_obtained, feedback):
        query = """
            UPDATE submissions
            SET marks_obtained = %s, feedback = %s, status = 'graded', graded_at = NOW()
            WHERE id = %s
        """
        return execute_query(query, (marks_obtained, feedback, submission_id), commit=True)
