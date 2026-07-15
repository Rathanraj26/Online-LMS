"""
test_db_connection.py
Standalone script to test your MySQL credentials WITHOUT running the full
Flask app. Run this first whenever you get a 1045 Access Denied error —
it isolates the problem to just the database connection.

Usage:
    cd Online-LMS/backend
    python test_db_connection.py
"""
import mysql.connector
from mysql.connector import Error

# ============================================================
# EDIT THESE THREE VALUES to match your actual MySQL setup,
# then run this file. Once it prints "SUCCESS", copy these
# exact same values into your .env file.
# ============================================================
DB_USER = "root"
DB_PASSWORD = "PUT_YOUR_ACTUAL_MYSQL_PASSWORD_HERE"
DB_HOST = "localhost"
DB_PORT = 3306
# ============================================================

print(f"Attempting to connect as '{DB_USER}'@'{DB_HOST}:{DB_PORT}' ...\n")

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    print("✅ SUCCESS — connected to MySQL!")
    print(f"   Copy these exact values into backend/.env:")
    print(f"   DB_USER={DB_USER}")
    print(f"   DB_PASSWORD={DB_PASSWORD}")

    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES LIKE 'rr_lms'")
    result = cursor.fetchone()
    if result:
        print("\n✅ 'rr_lms' database already exists.")
    else:
        print("\n⚠️  'rr_lms' database does NOT exist yet.")
        print("   Run this next: mysql -u root -p < database/schema.sql")

    cursor.close()
    conn.close()

except Error as e:
    print("❌ FAILED to connect.")
    print(f"   Error: {e}\n")

    if "Access denied" in str(e):
        print("   This means DB_USER / DB_PASSWORD above are wrong.")
        print("   Fix options:")
        print("   1. If you know your real MySQL root password, edit DB_PASSWORD above and re-run this script.")
        print("   2. If you don't know it, reset it via MySQL Workbench (a session that's already logged in) by running:")
        print("        ALTER USER 'root'@'localhost' IDENTIFIED BY 'NewPassword123';")
        print("        FLUSH PRIVILEGES;")
        print("      Then set DB_PASSWORD = 'NewPassword123' above and re-run this script.")
    elif "Can't connect" in str(e) or "10061" in str(e):
        print("   This means MySQL server itself isn't running.")
        print("   Start it via: Windows Services -> MySQL80 -> Start,")
        print("   or via XAMPP Control Panel -> MySQL -> Start.")
    else:
        print("   Check DB_HOST / DB_PORT above match your MySQL install.")
