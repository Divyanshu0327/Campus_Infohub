"""
Migration: Add password column to alumni table
Run this script ONCE to update the existing database schema.
Usage: python migrate_alumni_password.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "college_hub.db")


def migrate():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if password column already exists in alumni table
    cursor.execute("PRAGMA table_info(alumni)")
    columns = [row[1] for row in cursor.fetchall()]

    if "password" in columns:
        print("✅ 'password' column already exists in alumni table. No migration needed.")
        conn.close()
        return

    print("Adding 'password' column to alumni table...")
    cursor.execute("ALTER TABLE alumni ADD COLUMN password VARCHAR(255)")

    # Update existing Active alumni status to stay Active (no change needed)
    # Update existing alumni (registered before this migration) who don't have a password
    # They will need to use Forgot Password to set a password if they want to login
    cursor.execute(
        "UPDATE alumni SET status = 'Active' WHERE status = 'Active'"
    )

    conn.commit()
    conn.close()

    print("✅ Migration complete: 'password' column added to alumni table.")
    print("   Existing 'Active' alumni records retained. They can use Forgot Password to set a login password.")
    print("   New alumni registrations will require a password and will default to 'Pending' status.")


if __name__ == "__main__":
    migrate()
