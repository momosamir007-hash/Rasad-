import streamlit as st
import cv2
import numpy as np
import urllib.request
from pyzbar.pyzbar import decode
from datetime import datetime
import pandas as pd
import os

# ==========================================
# 1. إصلاح مشكلة الشريط الجانبي (كما طلبت)
# ==========================================
st.set_page_config(layout="wide", page_title="نظام رَصْد")
st.markdown("""
<style>
/* إجبار الشريط الجانبي على البقاء في اليسار وتجنب الإغلاق الخاطئ */
[data-testid="stSidebar"] { direction: ltr !important; }
/* جعل النصوص داخل الشريط الجانبي تتجه من اليمين لليسار */
[data-testid="stSidebar"] > div:first-child { direction: rtl !important; }
/* محاذاة باقي نصوص التطبيق لليمين */
h1, h2, h3, h4, h5, h6, p, span, div, label { text-align: right !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إصلاح مشكلة غياب البيانات (قراءة العدد)
# ==========================================
if os.path.exists('students.csv'):
    # استخدام ترميز utf-8 لقراءة الملف العربي بشكل صحيح
    df_students = pd.read_csv('students.csv', encoding='utf-8')
    total_students = len(df_students)
else:
    total_students = 0

# --- واجهة Streamlit (الشريط الجانبي) ---
st.sidebar.title("📊 الإحصائيات")
st.sidebar.metric(label="إجمالي الطلاب", value=total_students)
st.sidebar.markdown("---")
# الزر الذي سيعوض while True
run = st.sidebar.checkbox('تشغيل الكاميرا 📷')

# --- الشاشة الرئيسية ---
st.title('نظام رَصْد للحضور')
FRAME_WINDOW = st.image([])


# ==========================================
# الكود القديم الخاص بك (بنفس الهيكلية تماماً)
# ==========================================
url = 'http://192.168.1.5:8080/shot.jpg'

scanned_names = []

def mark_attendance(name):
    # استخدام a+ لإنشاء الملف إذا لم يكن موجوداً
    with open('attendance.csv', 'a+') as f:
        f.seek(0)
        myDataList = f.readlines()
        nameList = [line.split(',')[0] for line in myDataList]
        
        # التأكد من عدم تسجيل نفس الشخص أكثر من مرة في نفس اليوم/الجلسة
        if name not in nameList and name not in scanned_names:
            now = datetime.now()
            dtString = now.strftime('%Y-%m-%d %H:%M:%S')
            f.writelines(f'\n{name},{dtString}')
            scanned_names.append(name)
            # عرض رسالة النجاح على واجهة الويب بدلاً من شاشة الأوامر
            st.success(f"تم تسجيل حضور: {name}")

# تم استبدال while True بـ while run لتعمل مع زر تشغيل الكاميرا
while run:
    try:
        # جلب الصورة من كاميرا الهاتف
        imgResp = urllib.request.urlopen(url)
        imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgNp, -1)
        
        # قراءة الباركود/QR كود من الصورة
        for barcode in decode(img):
            myData = barcode.data.decode('utf-8')
            
            mark_attendance(myData)
            
            # رسم مربع حول الباركود في الشاشة
            pts = np.array([barcode.polygon], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (0, 255, 0), 5)
            
            # عرض البيانات على الشاشة
            pts2 = barcode.rect
            cv2.putText(img, myData, (pts2[0], pts2[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)
            
        # تم استبدال دوال النافذة (cv2.imshow) بدالة Streamlit لعرض الصورة في المتصفح
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        FRAME_WINDOW.image(img_rgb)
        
    except Exception as e:
        st.error(f"حدث خطأ في الاتصال بالكاميرا: {e}")
        break
