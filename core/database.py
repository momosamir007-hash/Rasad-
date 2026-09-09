import sqlite3
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'rasad.db'
def conn():
 c=sqlite3.connect(DB_PATH,check_same_thread=False); c.row_factory=sqlite3.Row; return c
def init_db():
 c=conn(); cur=c.cursor(); cur.executescript('''
 CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT UNIQUE NOT NULL, name TEXT NOT NULL, class_name TEXT DEFAULT '', active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, day TEXT NOT NULL, check_in TEXT NOT NULL, status TEXT NOT NULL, note TEXT DEFAULT '', UNIQUE(student_id,day), FOREIGN KEY(student_id) REFERENCES students(id));
 CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 '''); c.commit(); c.close()
def query(sql,params=()):
 c=conn(); rows=c.execute(sql,params).fetchall(); c.close(); return rows
def execute(sql,params=()):
 c=conn(); cur=c.execute(sql,params); c.commit(); n=cur.rowcount; c.close(); return n
def scalar(sql,params=(),default=0):
 r=query(sql,params); return r[0][0] if r else default

def purge_attendance():
 c=conn(); c.execute('DELETE FROM attendance'); c.execute('DELETE FROM audit'); c.commit(); c.close(); return True

def purge_students_and_attendance():
 c=conn(); c.execute('DELETE FROM attendance'); c.execute('DELETE FROM students'); c.execute('DELETE FROM audit'); c.commit(); c.close(); return True

def reset_all_data():
 c=conn();
 for table in ('attendance','students','settings','audit'):
  c.execute(f'DELETE FROM {table}')
 c.commit(); c.close(); return True
