import streamlit as st
import cv2
import numpy as np
import urllib.request
from pyzbar.pyzbar import decode
from datetime import datetime
import pandas as pd
import os

# ==========================================
# 1. إعدادات الصفحة وإصلاح مشكلة الشريط الجانبي
# ==========================================
st.set_page_config(page_title="نظام رَصْد للحضور", layout="wide", page_icon="🎓")

st.markdown("""
<style>
/* محاذاة النصوص الأساسية لليمين */
* {
    text-align: right;
    font-family: 'Arial', sans-serif;
}
h1, h2, h3, h4, h5, h6, p, span, div, label {
    text-align: right !important;
}

/* ⚠️ الحل الجذري لمشكلة الشريط الجانبي ⚠️ */
/* إجبار حاوية الشريط الجانبي على البقاء في اليسار لتجنب إغلاقه في المنتصف */
[data-testid="stSidebar"] {
    direction: ltr !important; 
}
/* جعل محتوى الشريط الجانبي يتجه من اليمين لليسار ليناسب اللغة العربية */
[data-testid="stSidebar"] > div:first-child {
    direction: rtl !important;
}

/* جعل الجداول تتجه من اليمين لليسار */
[data-testid="stDataFrame"] {
    direction: rtl !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعدادات الملفات ودوال جلب البيانات
# ==========================================
STUDENTS_FILE = 'students.csv'
ATTENDANCE_FILE = 'attendance.csv'

# دالة آمنة لتحميل بيانات الطلاب
@st.cache_data(ttl=60)
def load_students_data():
    if os.path.exists(STUDENTS_FILE):
        try:
            df = pd.read_csv(STUDENTS_FILE, encoding='utf-8')
            # إنشاء قاموس للبحث السريع عن اسم الطالب بواسطة الباركود (ID)
            students_dict = {}
            if 'ID' in df.columns and 'Name' in df.columns:
                for _, row in df.iterrows():
                    students_dict[str(row['ID']).strip()] = str(row['Name']).strip()
            return df, students_dict
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة البيانات: {e}")
            return pd.DataFrame(), {}
    else:
        st.warning(f"⚠️ لم يتم العثور على ملف {STUDENTS_FILE}. تأكد من وجوده في نفس المجلد.")
        return pd.DataFrame(), {}

# دالة لإنشاء ملف الحضور إذا لم يكن موجوداً
def init_attendance_file():
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['ID', 'Name', 'Time', 'Date'])
        df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')

# دالة لجلب قائمة من سجلوا حضورهم اليوم
def get_attended_today():
    if not os.path.exists(ATTENDANCE_FILE):
        return set()
    try:
        df = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
        if df.empty: 
            return set()
        today = datetime.now().strftime('%Y-%m-%d')
        today_records = df[df['Date'] == today]
        return set(today_records['ID'].astype(str).tolist())
    except:
        return set()

# دالة تسجيل الحضور في الملف
def mark_attendance(student_id, student_name):
    now = datetime.now()
    time_str = now.strftime('%H:%M:%S')
    date_str = now.strftime('%Y-%m-%d')
    
    new_record = pd.DataFrame({
        'ID': [student_id],
        'Name': [student_name],
        'Time': [time_str],
        'Date': [date_str]
    })
    # إضافة السجل الجديد للملف
    new_record.to_csv(ATTENDANCE_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')

# ==========================================
# 3. بناء واجهة المستخدم (الشاشة)
# ==========================================
init_attendance_file()
df_students, students_dict = load_students_data()

# حساب الإحصائيات
total_students = len(df_students) if not df_students.empty else 0
attended_today_set = get_attended_today()
total_attended = len(attended_today_set)
total_absent = total_students - total_attended if total_students > 0 else 0

st.title("🎓 نظام رَصْد - تسجيل الحضور والغياب")

# --- الشريط الجانبي ---
st.sidebar.header("⚙️ إعدادات الكاميرا")
camera_url = st.sidebar.text_input("رابط كاميرا الهاتف (IP Webcam):", value="http://192.168.1.5:8080/shot.jpg")
run = st.sidebar.checkbox('تشغيل الكاميرا لبدء المسح 📷')

st.sidebar.markdown("---")
st.sidebar.header("📊 إحصائيات اليوم")
st.sidebar.metric(label="إجمالي الطلاب المسجلين", value=total_students)
st.sidebar.metric(label="🟢 عدد الحاضرين", value=total_attended)
st.sidebar.metric(label="🔴 عدد الغائبين", value=total_absent)

# --- الشاشة الرئيسية ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📷 شاشة المسح الحي")
    frame_window = st.image([])
    status_text = st.empty()

with col2:
    st.subheader("📝 آخر من سجلوا الحضور")
    records_placeholder = st.empty()
    
    # دالة لتحديث جدول الحضور المعروض على الشاشة
    def update_records_display():
        if os.path.exists(ATTENDANCE_FILE):
            try:
                df_att = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
                today = datetime.now().strftime('%Y-%m-%d')
                today_att = df_att[df_att['Date'] == today]
                if not today_att.empty:
                    # عرض آخر 10 سجلات من الأحدث للأقدم
                    display_df = today_att.tail(10)[['Name', 'Time']].iloc[::-1]
                    display_df.columns = ['الاسم', 'وقت الحضور']
                    records_placeholder.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    records_placeholder.info("لم يسجل أحد حضوره اليوم بعد.")
            except:
                pass
    
    update_records_display()

# ==========================================
# 4. محرك الكاميرا وقراءة الباركود
# ==========================================
if run:
    status_text.info("⏳ جاري الاتصال بالكاميرا...")
    while run:
        try:
            # جلب الصورة من الكاميرا
            imgResp = urllib.request.urlopen(camera_url, timeout=5)
            imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
            img = cv2.imdecode(imgNp, -1)
            
            # البحث عن الباركود في الصورة
            for barcode in decode(img):
                student_id = barcode.data.decode('utf-8').strip()
                
                # رسم مربع حول الباركود على الشاشة
                pts = np.array([barcode.polygon], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(img, [pts], True, (0, 255, 0), 3)
                
                # معالجة تسجيل الحضور
                if student_id not in attended_today_set:
                    # جلب اسم الطالب من القاموس (وإلا سيعتبر مجهولاً)
                    student_name = students_dict.get(student_id, "طالب غير مسجل في النظام")
                    
                    # تسجيله في الملف والذاكرة
                    mark_attendance(student_id, student_name)
                    attended_today_set.add(student_id)
                    
                    # عرض رسالة نجاح وتحديث الجدول
                    status_text.success(f"✅ تم تسجيل حضور: {student_name}")
                    update_records_display()
                else:
                    student_name = students_dict.get(student_id, "طالب غير مسجل")
                    status_text.warning(f"⚠️ {student_name} مسجل مسبقاً اليوم!")
                    
            # تحويل ألوان الصورة لتعمل بشكل صحيح في Streamlit
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame_window.image(img_rgb)
            
        except urllib.error.URLError:
            status_text.error("❌ تعذر الاتصال بالكاميرا. تأكد من أن تطبيق IP Webcam يعمل، وأن الهاتف والحاسوب متصلان بنفس شبكة الواي فاي.")
            break
        except Exception as e:
            status_text.error(f"❌ حدث خطأ غير متوقع: {e}")
            break
else:
    status_text.info("الكاميرا متوقفة. قم بتفعيلها من الشريط الجانبي لبدء تسجيل الحضور.")
    # عرض صورة سوداء كخلفية عند توقف الكاميرا
    black_img = np.zeros((480, 640, 3), dtype=np.uint8)
    frame_window.image(black_img)
