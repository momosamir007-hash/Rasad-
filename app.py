import streamlit as st
from PIL import Image
from datetime import datetime
from database import initialize_database
from student_manager import get_students,add_student,import_students
from attendance_manager import mark_attendance,get_attendance
from barcode_scanner import scan_barcodes
from reports import get_daily_report
st.set_page_config(page_title='نظام رصد الحضور v2.0',page_icon='🎓',layout='wide')
st.markdown('<style>.block-container{direction:rtl}h1,h2,h3,p,label{text-align:right!important}</style>',unsafe_allow_html=True)
def main():
 initialize_database(); st.title('🎓 نظام رصد الحضور الذكي — v2.0'); st.caption('SQLite • منع التكرار • كشف التأخر • تقارير يومية')
 with st.sidebar:
  st.header('⚙️ التحكم'); late_time=st.text_input('وقت اعتبار الطالب متأخرًا','08:15'); st.divider(); up=st.file_uploader('📥 استيراد الطلاب Excel أو CSV',type=['xlsx','xls','csv'])
  if up and st.button('استيراد الملف'):
   r=import_students(up); st.success(f"أضيف {r['added']} | مكرر {r['duplicates']} | غير صالح {r['invalid']}") if r.get('success') else st.error(r.get('error'))
   if r.get('success'):st.rerun()
 report=get_daily_report(); cols=st.columns(5)
 for col,label,val in zip(cols,['🎓 الطلاب','✅ حاضر','❌ غائب','⏰ متأخر','📈 النسبة'],[report['total'],report['present'],report['absent'],report['late'],f"{report['rate']}%"]):col.metric(label,val)
 tabs=st.tabs(['📷 تسجيل الحضور','👥 إدارة الطلاب','📊 السجل','📋 التقرير'])
 with tabs[0]:
  method=st.radio('طريقة التسجيل',['⌨️ إدخال يدوي','📁 رفع صورة','📷 الكاميرا'],horizontal=True)
  if 'يدوي' in method:
   with st.form('manual',clear_on_submit=True):
    b=st.text_input('رقم الباركود'); go=st.form_submit_button('✅ تسجيل')
    if go:
     ok,msg=mark_attendance(b,late_time); st.success(msg) if ok else st.warning(msg)
  else:
   f=st.file_uploader('اختر صورة',type=['png','jpg','jpeg','bmp']) if 'رفع' in method else st.camera_input('التقط صورة')
   if f:
    im=Image.open(f);st.image(im,use_container_width=True)
    if st.button('🔍 مسح الرمز'):
     res=scan_barcodes(im)
     if not res:st.error('لم يتم اكتشاف رمز')
     for code,typ in res:
      ok,msg=mark_attendance(code,late_time);st.success(f'{typ}: {msg}') if ok else st.warning(f'{typ}: {msg}')
 with tabs[1]:
  with st.form('student',clear_on_submit=True):
   b=st.text_input('الباركود');n=st.text_input('الاسم');c=st.text_input('القسم');go=st.form_submit_button('➕ إضافة')
   if go:
    ok,msg=add_student(b,n,c);st.success(msg) if ok else st.error(msg)
    if ok:st.rerun()
  df=get_students();st.dataframe(df,use_container_width=True,hide_index=True)
 with tabs[2]:
  d=st.date_input('التاريخ',datetime.now().date());df=get_attendance(d);st.dataframe(df,use_container_width=True,hide_index=True)
  if not df.empty:st.download_button('⬇️ CSV',df.to_csv(index=False).encode('utf-8-sig'),f'attendance_{d}.csv','text/csv')
 with tabs[3]:
  d=st.date_input('تاريخ التقرير',datetime.now().date(),key='rdate');r=get_daily_report(d);st.metric('نسبة الحضور',f"{r['rate']}%")
  st.subheader('❌ الغائبون');st.dataframe(r['absent_students'],use_container_width=True,hide_index=True)
if __name__=='__main__':main()
