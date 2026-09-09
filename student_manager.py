import pandas as pd
from datetime import datetime
from database import get_connection

def norm(v):
    if pd.isna(v): return ''
    s=str(v).strip()
    return s[:-2] if s.endswith('.0') and s[:-2].isdigit() else s

def get_students():
    with get_connection() as c: rows=c.execute('SELECT id,barcode,name,class_name FROM students ORDER BY name').fetchall()
    return pd.DataFrame([dict(x) for x in rows])
def add_student(barcode,name,class_name=''):
    barcode,name=norm(barcode),str(name).strip()
    if not barcode or not name:return False,'الباركود والاسم مطلوبان'
    try:
        with get_connection() as c:c.execute('INSERT INTO students(barcode,name,class_name,created_at) VALUES(?,?,?,?)',(barcode,name,str(class_name).strip(),datetime.now().isoformat(timespec='seconds')))
        return True,'تمت إضافة الطالب بنجاح'
    except Exception as e:return False,'الباركود مسجل مسبقًا' if 'UNIQUE' in str(e) else str(e)
def import_students(file):
    try: df=pd.read_excel(file,dtype=object)
    except Exception: file.seek(0); df=pd.read_csv(file,dtype=object)
    df.columns=[str(c).strip().lower() for c in df.columns]
    def find(names): return next((x for x in names if x in df.columns),None)
    bc=find(['barcode','id','رقم','كود','code','student_id','رقم الباركود']) or (df.columns[0] if len(df.columns)>0 else None)
    nm=find(['name','اسم','الاسم','student_name','اسم الطالب']) or (df.columns[1] if len(df.columns)>1 else None)
    cl=find(['class','القسم','الفوج','القسم الدراسي'])
    if not bc or not nm:return {'success':False,'error':'تعذر تحديد عمود الباركود والاسم'}
    added=duplicates=invalid=0; seen=set()
    for _,r in df.iterrows():
        b,n=norm(r.get(bc)),str(r.get(nm,'')).strip()
        cn=str(r.get(cl,'')).strip() if cl else ''
        if not b or b.lower() in ('nan','none') or not n or n.lower() in ('nan','none'):invalid+=1;continue
        if b in seen:duplicates+=1;continue
        seen.add(b); ok,_=add_student(b,n,cn); added+=int(ok); duplicates+=int(not ok)
    return {'success':True,'total':len(df),'added':added,'duplicates':duplicates,'invalid':invalid}
