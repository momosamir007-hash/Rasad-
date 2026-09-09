import sqlite3
from contextlib import contextmanager
from datetime import datetime
DB_FILE='attendance.db'
@contextmanager
def get_connection():
    conn=sqlite3.connect(DB_FILE,check_same_thread=False); conn.row_factory=sqlite3.Row
    try: yield conn; conn.commit()
    finally: conn.close()
def initialize_database():
    with get_connection() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,barcode TEXT NOT NULL UNIQUE,name TEXT NOT NULL,class_name TEXT DEFAULT '',created_at TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER NOT NULL,barcode TEXT NOT NULL,name TEXT NOT NULL,attendance_date TEXT NOT NULL,check_in TEXT NOT NULL,status TEXT NOT NULL,UNIQUE(student_id,attendance_date))''')
