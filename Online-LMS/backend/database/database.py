"""
database.py
Handles MySQL connections and provides a simple query helper used by all models.
"""
import mysql.connector
from mysql.connector import pooling, Error
from config import config

_pool = None


def init_pool():
    """Initialize a MySQL connection pool. Called once at app startup."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="rr_lms_pool",
            pool_size=10,
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            autocommit=True,
        )
    return _pool


def get_connection():
    """Return a pooled MySQL connection."""
    pool = init_pool()
    return pool.get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Generic query executor.

    Args:
        query (str): SQL query with %s placeholders.
        params (tuple|list): Query parameters.
        fetch_one (bool): Return a single row (dict).
        fetch_all (bool): Return all rows (list of dicts).
        commit (bool): Commit after execution (INSERT/UPDATE/DELETE).

    Returns:
        dict | list | int: query result, or last inserted row id for INSERT.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid if commit else cursor.rowcount

        if commit:
            conn.commit()

        return result
    except Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
