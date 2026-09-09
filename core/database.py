import sqlite3
from pathlib import Path


# ============================================================
# إعداد قاعدة البيانات
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "rasad.db"


def conn():
    """إنشاء اتصال جديد بقاعدة البيانات."""

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    # تفعيل العلاقات الخارجية في SQLite
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# إنشاء الجداول
# ============================================================

def init_db():

    connection = conn()
    cursor = connection.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            class_name TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            check_in TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT DEFAULT '',

            UNIQUE(student_id, day),

            FOREIGN KEY(student_id)
            REFERENCES students(id)
            ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()
    connection.close()


# ============================================================
# الاستعلامات
# ============================================================

def query(sql, params=()):

    connection = conn()

    try:
        rows = connection.execute(
            sql,
            params
        ).fetchall()

        return rows

    finally:
        connection.close()


def execute(sql, params=()):

    connection = conn()

    try:

        cursor = connection.execute(
            sql,
            params
        )

        connection.commit()

        return cursor.rowcount

    finally:
        connection.close()


def scalar(sql, params=(), default=0):

    rows = query(sql, params)

    if rows:
        return rows[0][0]

    return default


# ============================================================
# 🧹 إدارة البيانات
# ============================================================

def purge_attendance():
    """حذف سجل الحضور وسجل العمليات فقط."""

    connection = conn()

    try:

        connection.execute(
            "DELETE FROM attendance"
        )

        connection.execute(
            "DELETE FROM audit"
        )

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


def purge_students_and_attendance():
    """حذف الطلاب والحضور وسجل العمليات."""

    connection = conn()

    try:

        # الحضور أولاً بسبب العلاقة مع الطلاب
        connection.execute(
            "DELETE FROM attendance"
        )

        connection.execute(
            "DELETE FROM students"
        )

        connection.execute(
            "DELETE FROM audit"
        )

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


def reset_all_data():
    """إعادة ضبط النظام بالكامل."""

    connection = conn()

    try:

        # ترتيب الحذف مهم
        tables = [
            "attendance",
            "students",
            "settings",
            "audit"
        ]

        for table in tables:

            connection.execute(
                f"DELETE FROM {table}"
            )

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()
