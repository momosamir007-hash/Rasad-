from datetime import datetime
from student_manager import get_students
from attendance_manager import get_attendance

def get_daily_report(date_value=None):
 day=str(date_value or datetime.now().date()); students=get_students(); att=get_attendance(day)
 total=len(students); present=len(att); late=int((att['status']=='متأخر').sum()) if not att.empty else 0
 codes=set(att['barcode'].astype(str)) if not att.empty else set()
 absent=students[~students['barcode'].astype(str).isin(codes)] if not students.empty else students
 return {'date':day,'total':total,'present':present,'late':late,'absent':max(total-present,0),'rate':round(present/total*100,1) if total else 0,'attendance':att,'absent_students':absent}
