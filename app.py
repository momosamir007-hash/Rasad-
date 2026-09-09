import streamlit as st
import pandas as pd
from datetime import datetime,date
from core.database import (
    init_db,
    query,
    purge_attendance,
    purge_students_and_attendance,
    reset_all_data
)
from services.app_service import *
from components.ui import css,hero
st.set_page_config(page_title='رَصْد | منصة الحضور الذكية',page_icon='🎓',layout='wide',initial_sidebar_state='expanded')
init_db(); css()
if 'page' not in st.session_state:st.session_state.page='🏠 لوحة القيادة'
PAGES=['🏠 لوحة القيادة','⚡ مركز الحضور','👨‍🎓 إدارة الطلاب','📅 السجل والغياب','📊 التحليلات والتقارير','🔔 التنبيهات','⚙️ الإعدادات']
with st.sidebar:
 st.markdown('## 🎓 رَصْد'); st.caption('منصة الحضور المدرسية الذكية • v3.0');
 for p in PAGES:
  if st.button(p,key='nav_'+p,use_container_width=True):st.session_state.page=p
 st.divider();st.caption('🔒 البيانات محفوظة محليًا في SQLite')
p=st.session_state.page
if p=='🏠 لوحة القيادة':
 hero('🏠 صباح الخير، مرحبًا بك في رَصْد','لوحة متابعة مباشرة للحضور والغياب والتأخر')
 d=dashboard(); c=st.columns(5)
 for col,(lab,val) in zip(c,[('👨‍🎓 إجمالي الطلاب',d['total']),('✅ حاضر اليوم',d['present']),('❌ الغائبون',d['absent']),('⏰ متأخرون',d['late']),('📈 نسبة الحضور',str(d['rate'])+'%')]):col.metric(lab,val)
 st.divider(); a,b=st.columns([1.35,1])
 with a:
  st.subheader('📈 اتجاه الحضور'); tr=trends(14); st.line_chart(tr.set_index('day')[['present','late']] if not tr.empty else pd.DataFrame({'present':[]}))
 with b:
  st.subheader('🕒 آخر عمليات التسجيل'); x=today_rows(); st.dataframe(x.head(8),hide_index=True,use_container_width=True)
 st.subheader('⚡ إجراءات سريعة'); q1,q2,q3=st.columns(3)
 if q1.button('➕ إضافة طالب',use_container_width=True):st.session_state.page='👨‍🎓 إدارة الطلاب';st.rerun()
 if q2.button('📷 تسجيل حضور',use_container_width=True):st.session_state.page='⚡ مركز الحضور';st.rerun()
 if q3.button('📊 تقرير اليوم',use_container_width=True):st.session_state.page='📊 التحليلات والتقارير';st.rerun()
elif p=='⚡ مركز الحضور':
 hero('⚡ مركز تسجيل الحضور','سريع، مباشر، ويمنع التسجيل المكرر تلقائيًا')
 late=get_setting('late_time','08:15'); m=st.radio('طريقة التسجيل',['⌨️ إدخال سريع','📷 كاميرا / صورة'],horizontal=True)
 if m=='⌨️ إدخال سريع':
  left,right=st.columns([1,1])
  with left:
   with st.form('scan',clear_on_submit=True):
    code=st.text_input('🆔 امسح أو أدخل الباركود',placeholder='مثال: S001'); status=st.selectbox('الحالة',['تلقائي','حاضر','متأخر','مستأذن','نشاط']); note=st.text_input('ملاحظة اختيارية'); go=st.form_submit_button('🚀 تسجيل الآن',use_container_width=True)
    if go:
     ok,msg,s=mark(code,late,None if status=='تلقائي' else status,note)
     if ok:st.success('✅ '+msg);st.balloons()
     else:st.warning('⚠️ '+msg)
  with right:
   st.subheader('آخر التسجيلات');st.dataframe(today_rows().head(12),hide_index=True,use_container_width=True)
 else:
  st.info('نسخة v3 تعتمد QR عبر OpenCV بدون حزم Linux إضافية. للباركود التقليدي استخدم قارئ USB أو الإدخال السريع.'); f=st.camera_input('التقط رمز QR') or st.file_uploader('أو ارفع صورة',type=['png','jpg','jpeg'])
  if f:
   import cv2,numpy as np
   from PIL import Image
   im=Image.open(f).convert('RGB'); data,_,_=cv2.QRCodeDetector().detectAndDecode(np.array(im))
   if data:
    ok,msg,s=mark(data,late);st.success(msg) if ok else st.warning(msg)
   else:st.error('لم يتم اكتشاف QR واضح')
elif p=='👨‍🎓 إدارة الطلاب':
 hero('👨‍🎓 إدارة الطلاب','إضافة وتعديل واستيراد وبحث في قاعدة بيانات موحدة')
 t1,t2=st.tabs(['👥 قاعدة الطلاب','📥 استيراد جماعي'])
 with t1:
  c1,c2=st.columns([1.5,1]); search=c1.text_input('🔎 ابحث بالاسم أو الباركود أو القسم');
  with c2:
   with st.expander('➕ إضافة طالب'):
    with st.form('addstudent',clear_on_submit=True):
     b=st.text_input('الباركود');n=st.text_input('الاسم');cl=st.text_input('القسم');go=st.form_submit_button('حفظ')
     if go:
      ok,msg=add_student(b,n,cl);st.success(msg) if ok else st.error(msg);st.rerun() if ok else None
  df=students(search);st.dataframe(df,hide_index=True,use_container_width=True,height=430)
  if not df.empty:
   st.download_button('⬇️ تصدير الطلاب CSV',df.to_csv(index=False).encode('utf-8-sig'),'students.csv','text/csv')
   ids=dict(zip(df['name']+' | '+df['barcode'],df['id'])); chosen=st.selectbox('✏️ اختر طالبًا للتعديل',list(ids),index=None)
   if chosen:
    row=df[df.id==ids[chosen]].iloc[0]
    with st.form('edit'):
     b=st.text_input('الباركود',row.barcode);n=st.text_input('الاسم',row.name);cl=st.text_input('القسم',row.class_name); save=st.form_submit_button('💾 حفظ التعديلات')
     if save:ok,msg=update_student(int(row.id),b,n,cl);st.success(msg) if ok else st.error(msg);st.rerun() if ok else None
    if st.button('🗑️ إيقاف الطالب',key='del_'+str(row.id)):delete_student(int(row.id));st.rerun()
 with t2:
  f=st.file_uploader('Excel أو CSV',type=['xlsx','xls','csv']);
  if f and st.button('🚀 بدء الاستيراد'):ok,msg=import_file(f);st.success(msg) if ok else st.error(msg)
elif p=='📅 السجل والغياب':
 hero('📅 السجل والغياب','متابعة يومية مع قائمة الغائبين والتصدير')
 d=st.date_input('اختر التاريخ',date.today()); rows=today_rows(d); ab=absentees(d); a,b=st.columns(2)
 with a:st.subheader(f'✅ المسجلون ({len(rows)})');st.dataframe(rows,hide_index=True,use_container_width=True)
 with b:st.subheader(f'❌ الغائبون ({len(ab)})');st.dataframe(ab,hide_index=True,use_container_width=True)
 c1,c2=st.columns(2);c1.download_button('⬇️ تحميل سجل الحضور',rows.to_csv(index=False).encode('utf-8-sig'),f'attendance_{d}.csv');c2.download_button('⬇️ تحميل الغياب',ab.to_csv(index=False).encode('utf-8-sig'),f'absent_{d}.csv')
elif p=='📊 التحليلات والتقارير':
 hero('📊 مركز التحليلات','تحويل بيانات الحضور إلى مؤشرات قابلة للمتابعة')
 tr=trends(30); d=dashboard(); st.metric('نسبة حضور اليوم',str(d['rate'])+'%');
 if not tr.empty:st.bar_chart(tr.set_index('day')[['present','late']]);st.dataframe(tr,hide_index=True,use_container_width=True)
 st.subheader('🏫 أداء الأقسام اليوم'); x=today_rows();
 if not x.empty:st.dataframe(x.groupby('class_name').size().reset_index(name='عدد التسجيلات'),hide_index=True,use_container_width=True)
 st.subheader('📋 ملخص ذكي محلي'); st.info(f"اليوم تم تسجيل {d['present']} من أصل {d['total']} طالب، بنسبة حضور {d['rate']}%. عدد المتأخرين: {d['late']}. يمكن لاحقًا إرسال هذا الملخص إلى مزود ذكاء اصطناعي اختياري من صفحة الإعدادات.")
elif p=='🔔 التنبيهات':
 hero('🔔 مركز التنبيهات','اكتشاف الحالات التي تحتاج إلى متابعة')
 al=alerts();
 if al.empty:st.success('🎉 لا توجد حالات غياب متكرر كافية لإنشاء تنبيه بعد.')
 else:st.warning('⚠️ الطلاب الذين ظهر لديهم غياب متكرر في الأيام المسجلة');st.dataframe(al,hide_index=True,use_container_width=True)
 st.subheader('📌 تنبيهات اليوم');d=dashboard();
 if d['absent']:st.info(f"يوجد {d['absent']} طالبًا لم يسجلوا حضورهم اليوم.")
 if d['late']:st.info(f"يوجد {d['late']} حالة تأخر اليوم.")
elif p=='⚙️ الإعدادات':
 hero('⚙️ إعدادات المنصة','تحكم في قواعد الحضور وتجهيز التكاملات القادمة')
 with st.form('settings'):
  late=st.text_input('وقت اعتبار الطالب متأخرًا',get_setting('late_time','08:15')); provider=st.selectbox('مزود الذكاء الاصطناعي المستقبلي',[get_setting('ai_provider','محلي'),'محلي','OpenRouter','Mistral']); model=st.text_input('النموذج الافتراضي',get_setting('ai_model',''))
  save=st.form_submit_button('💾 حفظ الإعدادات')
  if save:set_setting('late_time',late);set_setting('ai_provider',provider);set_setting('ai_model',model);st.success('تم حفظ الإعدادات')
 st.divider()
 st.subheader('🧹 مركز إدارة البيانات')
 st.warning('⚠️ استخدم هذه الخيارات بحذر. الحذف لا يمكن التراجع عنه.')
 r1,r2,r3=st.columns(3)
 with r1:
  st.caption('يحذف سجلات الحضور فقط ويُبقي الطلاب والإعدادات.')
  if st.button('🗑️ مسح سجل الحضور',use_container_width=True):
   st.session_state.confirm_action='attendance'
 with r2:
  st.caption('يحذف جميع الطلاب وسجلات الحضور المرتبطة بهم.')
  if st.button('👥🗑️ حذف الطلاب والحضور',use_container_width=True):
   st.session_state.confirm_action='students'
 with r3:
  st.caption('يعيد النظام إلى حالة فارغة تمامًا.')
  if st.button('🔥 إعادة ضبط النظام بالكامل',use_container_width=True):
   st.session_state.confirm_action='all'
 action=st.session_state.get('confirm_action')
 if action:
  labels={'attendance':'مسح سجل الحضور فقط','students':'حذف جميع الطلاب وسجلات الحضور','all':'إعادة ضبط النظام بالكامل'}
  st.error('تأكيد العملية: '+labels[action])
  phrase=st.text_input('اكتب كلمة تأكيد الحذف: حذف البيانات',key='confirm_phrase')
  c1,c2=st.columns(2)
  if c1.button('✅ تأكيد الحذف',type='primary',use_container_width=True):
   if phrase.strip()=='حذف البيانات':
    if action=='attendance': purge_attendance(); msg='تم مسح سجل الحضور.'
    elif action=='students': purge_students_and_attendance(); msg='تم حذف الطلاب وسجلات الحضور.'
    else: reset_all_data(); msg='تمت إعادة ضبط النظام بالكامل.'
    st.session_state.pop('confirm_action',None); st.success(msg); st.rerun()
   else: st.error('عبارة التأكيد غير صحيحة.')
  if c2.button('إلغاء',use_container_width=True):
   st.session_state.pop('confirm_action',None); st.rerun()
 st.divider();st.subheader('🛠️ سجل العمليات'); au=query('SELECT action,details,created_at FROM audit ORDER BY id DESC LIMIT 30');st.dataframe(pd.DataFrame([dict(x) for x in au]),hide_index=True,use_container_width=True)
