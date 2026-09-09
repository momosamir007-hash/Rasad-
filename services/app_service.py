import pandas as pd
from datetime import datetime, date, time
from core.database import query,execute,scalar

def norm(v):
 if pd.isna(v): return ''
 s=str(v).strip()
 return s[:-2] if s.endswith('.0') and s[:-2].isdigit() else s

def students(search=''):
 sql='SELECT id,barcode,name,class_name,active,created_at FROM students WHERE active=1'; p=[]
 if search: sql+=' AND (name LIKE ? OR barcode LIKE ? OR class_name LIKE ?)'; p=['%'+search+'%']*3
 return pd.DataFrame([dict(x) for x in query(sql,p)])
def add_student(barcode,name,class_name=''):
 barcode,norm_name=norm(barcode),norm(name)
 if not barcode or not norm_name:return False,'أدخل الباركود والاسم'
 try: execute('INSERT INTO students(barcode,name,class_name) VALUES(?,?,?)',(barcode,norm_name,norm(class_name))); audit('إضافة طالب',norm_name); return True,'تمت إضافة الطالب'
 except Exception:return False,'الباركود موجود مسبقًا'
def update_student(i,barcode,name,cls):
 if not norm(barcode) or not norm(name):return False,'البيانات ناقصة'
 try: execute('UPDATE students SET barcode=?,name=?,class_name=? WHERE id=?',(norm(barcode),norm(name),norm(cls),i));audit('تعديل طالب',norm(name));return True,'تم الحفظ'
 except Exception:return False,'الباركود مستخدم لطالب آخر'
def delete_student(i): execute('UPDATE students SET active=0 WHERE id=?',(i,));audit('إيقاف طالب',str(i));return True
def import_file(f):
 try: df=pd.read_csv(f) if f.name.lower().endswith('.csv') else pd.read_excel(f)
 except Exception as e:return False,str(e)
 cols={str(c).strip().lower():c for c in df.columns}; bc=next((cols[x] for x in ['barcode','id','code','student_id','رقم','الكود','باركود'] if x in cols),df.columns[0]); nm=next((cols[x] for x in ['name','student_name','الاسم','اسم الطالب'] if x in cols),df.columns[1] if len(df.columns)>1 else None); cl=next((cols[x] for x in ['class','class_name','section','القسم','الفوج'] if x in cols),None)
 if nm is None:return False,'لم يتم العثور على عمود الاسم'
 added=dup=bad=0
 for _,r in df.iterrows():
  ok,msg=add_student(r[bc],r[nm],r[cl] if cl else '')
  if ok:added+=1
  elif 'موجود' in msg:dup+=1
  else:bad+=1
 return True,f'أضيف {added} • مكرر {dup} • غير صالح {bad}'
def mark(barcode,late_time='08:15',status_override=None,note=''):
 rows=query('SELECT id,name,class_name FROM students WHERE barcode=? AND active=1',(norm(barcode),))
 if not rows:return False,'الرمز غير مسجل',None
 s=rows[0]; now=datetime.now(); day=now.date().isoformat(); st=status_override or ('متأخر' if now.time()>datetime.strptime(late_time,'%H:%M').time() else 'حاضر')
 try: execute('INSERT INTO attendance(student_id,day,check_in,status,note) VALUES(?,?,?,?,?)',(s['id'],day,now.strftime('%Y-%m-%d %H:%M:%S'),st,note));audit('تسجيل حضور',s['name']);return True,f"{st}: {s['name']}",dict(s)
 except Exception:return False,f"{s['name']} مسجل مسبقًا اليوم",dict(s)
def today_rows(d=None):
 d=(d or date.today()).isoformat(); return pd.DataFrame([dict(x) for x in query('SELECT a.id,s.name,s.barcode,s.class_name,a.check_in,a.status,a.note FROM attendance a JOIN students s ON s.id=a.student_id WHERE a.day=? ORDER BY a.check_in DESC',(d,))])
def dashboard(d=None):
 d=(d or date.today()).isoformat(); total=scalar('SELECT COUNT(*) FROM students WHERE active=1'); present=scalar('SELECT COUNT(*) FROM attendance WHERE day=?',(d,)); late=scalar("SELECT COUNT(*) FROM attendance WHERE day=? AND status='متأخر'",(d,)); return {'total':total,'present':present,'late':late,'absent':max(total-present,0),'rate':round(100*present/total,1) if total else 0}
def absentees(d=None):
 d=(d or date.today()).isoformat(); return pd.DataFrame([dict(x) for x in query('SELECT s.name,s.barcode,s.class_name FROM students s WHERE s.active=1 AND s.id NOT IN (SELECT student_id FROM attendance WHERE day=?) ORDER BY s.name',(d,))])
def trends(days=14):
 rows=query('SELECT day,COUNT(*) present,SUM(CASE WHEN status="متأخر" THEN 1 ELSE 0 END) late FROM attendance GROUP BY day ORDER BY day DESC LIMIT ?',(days,)); df=pd.DataFrame([dict(x) for x in rows]); return df.sort_values('day') if not df.empty else df
def alerts():
 rows=query('''SELECT s.name,s.class_name,COUNT(*) misses FROM students s CROSS JOIN (SELECT DISTINCT day FROM attendance) d WHERE s.active=1 AND NOT EXISTS(SELECT 1 FROM attendance a WHERE a.student_id=s.id AND a.day=d.day) GROUP BY s.id HAVING COUNT(*)>=3 ORDER BY misses DESC LIMIT 10'''); return pd.DataFrame([dict(x) for x in rows])
def audit(action,details):execute('INSERT INTO audit(action,details) VALUES(?,?)',(action,details))
def get_setting(k,default=''): r=query('SELECT value FROM settings WHERE key=?',(k,));return r[0]['value'] if r else default
def set_setting(k,v):execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,str(v)))
