from datetime import datetime
import pandas as pd
from database import get_connection

def mark_attendance(barcode,late_time='08:15'):
    barcode=str(barcode).strip()
    with get_connection() as c:
        s=c.execute('SELECT id,barcode,name FROM students WHERE barcode=?',(barcode,)).fetchone()
        if not s:return False,'باركود خارجي غير مسجل في قائمة الطلاب'
        now=datetime.now(); day=now.strftime('%Y-%m-%d')
        if c.execute('SELECT id FROM attendance WHERE student_id=? AND attendance_date=?',(s['id'],day)).fetchone():return False,f"{s['name']} مسجل مسبقًا اليوم"
        status='متأخر' if now.strftime('%H:%M')>late_time else 'حاضر'
        c.execute('INSERT INTO attendance(student_id,barcode,name,attendance_date,check_in,status) VALUES(?,?,?,?,?,?)',(s['id'],s['barcode'],s['name'],day,now.strftime('%Y-%m-%d %H:%M:%S'),status))
    return True,f"{s['name']} — {status}"
def get_attendance(date_value=None):
    with get_connection() as c:
        if date_value:rows=c.execute('SELECT barcode,name,attendance_date,check_in,status FROM attendance WHERE attendance_date=? ORDER BY check_in DESC',(str(date_value),)).fetchall()
        else:rows=c.execute('SELECT barcode,name,attendance_date,check_in,status FROM attendance ORDER BY check_in DESC').fetchall()
    return pd.DataFrame([dict(x) for x in rows])
