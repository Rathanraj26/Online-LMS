"""
course_model.py
Data-access layer for `courses`, `lessons`, and `enrollments`.
"""
from database.database import execute_query


class CourseModel:

    # ---------------- Courses ----------------
    @staticmethod
    def create(title, description, category, thumbnail, price, instructor_id):
        query = """
            INSERT INTO courses (title, description, category, thumbnail, price, instructor_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'published')
        """
        return execute_query(
            query, (title, description, category, thumbnail, price, instructor_id), commit=True
        )

    @staticmethod
    def get_all(search=None, category=None):
        query = """
            SELECT c.*, u.name AS instructor_name,
                   (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS enrolled_count
            FROM courses c
            JOIN users u ON u.id = c.instructor_id
            WHERE c.status = 'published'
        """
        params = []
        if search:
            query += " AND (c.title LIKE %s OR c.description LIKE %s)"
            params += [f"%{search}%", f"%{search}%"]
        if category:
            query += " AND c.category = %s"
            params.append(category)
        query += " ORDER BY c.created_at DESC"
        return execute_query(query, tuple(params), fetch_all=True)

    @staticmethod
    def get_by_id(course_id):
        query = """
            SELECT c.*, u.name AS instructor_name, u.email AS instructor_email
            FROM courses c
            JOIN users u ON u.id = c.instructor_id
            WHERE c.id = %s
        """
        return execute_query(query, (course_id,), fetch_one=True)

    @staticmethod
    def get_by_instructor(instructor_id):
        query = "SELECT * FROM courses WHERE instructor_id = %s ORDER BY created_at DESC"
        return execute_query(query, (instructor_id,), fetch_all=True)

    @staticmethod
    def update(course_id, title, description, category, price, status):
        query = """
            UPDATE courses
            SET title = %s, description = %s, category = %s, price = %s, status = %s
            WHERE id = %s
        """
        return execute_query(
            query, (title, description, category, price, status, course_id), commit=True
        )

    @staticmethod
    def delete(course_id):
        query = "DELETE FROM courses WHERE id = %s"
        return execute_query(query, (course_id,), commit=True)

    @staticmethod
    def count_all():
        query = "SELECT COUNT(*) AS total FROM courses"
        return execute_query(query, fetch_one=True)

    # ---------------- Lessons ----------------
    @staticmethod
    def add_lesson(course_id, title, lesson_type, file_path, duration_min, position):
        query = """
            INSERT INTO lessons (course_id, title, type, file_path, duration_min, position)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return execute_query(
            query, (course_id, title, lesson_type, file_path, duration_min, position), commit=True
        )

    @staticmethod
    def get_lessons(course_id):
        query = "SELECT * FROM lessons WHERE course_id = %s ORDER BY position ASC"
        return execute_query(query, (course_id,), fetch_all=True)

    @staticmethod
    def delete_lesson(lesson_id, course_id):
        query = "DELETE FROM lessons WHERE id = %s AND course_id = %s"
        return execute_query(query, (lesson_id, course_id), commit=True)

    # ---------------- Enrollments ----------------
    @staticmethod
    def enroll(user_id, course_id):
        query = "INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s)"
        return execute_query(query, (user_id, course_id), commit=True)

    @staticmethod
    def is_enrolled(user_id, course_id):
        query = "SELECT id FROM enrollments WHERE user_id = %s AND course_id = %s"
        return execute_query(query, (user_id, course_id), fetch_one=True)

    @staticmethod
    def get_enrolled_courses(user_id):
        query = """
            SELECT c.*, e.enrolled_at, u.name AS instructor_name
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            JOIN users u ON u.id = c.instructor_id
            WHERE e.user_id = %s
            ORDER BY e.enrolled_at DESC
        """
        return execute_query(query, (user_id,), fetch_all=True)

    @staticmethod
    def get_enrolled_students(course_id):
        query = """
            SELECT u.id, u.name, u.email, e.enrolled_at
            FROM enrollments e
            JOIN users u ON u.id = e.user_id
            WHERE e.course_id = %s
        """
        return execute_query(query, (course_id,), fetch_all=True)
