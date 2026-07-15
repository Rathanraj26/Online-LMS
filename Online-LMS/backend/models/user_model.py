"""
user_model.py
Data-access layer for the `users` table.
"""
from database.database import execute_query


class UserModel:

    @staticmethod
    def create(name, email, hashed_password, role="student"):
        query = """
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """
        return execute_query(query, (name, email, hashed_password, role), commit=True)

    @staticmethod
    def find_by_email(email):
        query = "SELECT * FROM users WHERE email = %s"
        return execute_query(query, (email,), fetch_one=True)

    @staticmethod
    def find_by_id(user_id):
        query = """
            SELECT id, name, email, role, phone, bio, avatar, is_active, created_at
            FROM users WHERE id = %s
        """
        return execute_query(query, (user_id,), fetch_one=True)

    @staticmethod
    def get_all(role=None):
        if role:
            query = """SELECT id, name, email, role, is_active, created_at
                       FROM users WHERE role = %s ORDER BY created_at DESC"""
            return execute_query(query, (role,), fetch_all=True)
        query = """SELECT id, name, email, role, is_active, created_at
                   FROM users ORDER BY created_at DESC"""
        return execute_query(query, fetch_all=True)

    @staticmethod
    def update_profile(user_id, name=None, phone=None, bio=None, avatar=None):
        fields, params = [], []
        if name is not None:
            fields.append("name = %s"); params.append(name)
        if phone is not None:
            fields.append("phone = %s"); params.append(phone)
        if bio is not None:
            fields.append("bio = %s"); params.append(bio)
        if avatar is not None:
            fields.append("avatar = %s"); params.append(avatar)

        if not fields:
            return 0

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        return execute_query(query, tuple(params), commit=True)

    @staticmethod
    def set_active_status(user_id, is_active: bool):
        query = "UPDATE users SET is_active = %s WHERE id = %s"
        return execute_query(query, (int(is_active), user_id), commit=True)

    @staticmethod
    def delete(user_id):
        query = "DELETE FROM users WHERE id = %s"
        return execute_query(query, (user_id,), commit=True)

    @staticmethod
    def count_by_role():
        query = "SELECT role, COUNT(*) AS total FROM users GROUP BY role"
        return execute_query(query, fetch_all=True)
