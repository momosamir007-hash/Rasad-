import streamlit as st
import cv2
import numpy as np
import urllib.request
from pyzbar.pyzbar import decode
from datetime import datetime
import pandas as pd
import os

# ==========================================
# التعديل 1: إصلاح الشريط الجانبي واللغة العربية
# ==========================================
st.set_page_config(page_title="نظام رَصْد للحضور", layout="wide", page_icon="🎓")

st.markdown("""
<style>
/* إجبار الشريط الجانبي على البقاء في اليسار وتجنب الإغلاق في المنتصف */
[data-testid="stSidebar"] {
    direction: ltr !important; 
}
/* جعل النصوص داخل الشريط الجانبي تتجه من اليمين لليسار */
[data-testid="stSidebar"] > div:first-child {
    direction: rtl !important;
}
/* محاذاة كل النصوص لليمين */
h1, h2, h3, h4, h5, h6, p, span, div, label {
    text-align: right !important;
}
/* جعل الجداول تتجه من اليمين لليسار */
[data-testid="stDataFrame"] {
    direction: rtl !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# الملفات الأساسية
# ==========================================
STUDENTS_FILE = 'students.csv'
ATTENDANCE_FILE = 'attendance.csv'

# ==========================================
# التعديل 2: قراءة البيانات بشكل صحيح (utf-8)
# ==========================================
@st.cache_data(ttl=60)
def load_students_data():
    if os.path.exists(STUDENTS_FILE):
        try:
            # إضافة encoding='utf-8' ليقرأ الأسماء العربية بدون أخطاء
            df = pd.read_csv(STUDENTS_FILE, encoding='utf-8')
            students_dict = {}
            if 'ID' in df.columns and 'Name' in df.columns:
                for _, row in df.iterrows():
                    students_dict[str(row['ID']).strip()] = str(row['Name']).strip()
            return df, students_dict
        except Exception as e:
            st.error(f"خطأ في قراءة ملف الطلاب: {e}")
            return pd.DataFrame(), {}
    else:
        return pd.DataFrame(), {}

def init_attendance_file():
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['ID', 'Name', 'Time', 'Date'])
        df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')

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

def mark_attendance(student_id, student_name):
    now = datetime.now()
    time_str = now.strftime('%H:%M:%S')
    date_str = now.strftime('%Y-%m-%d')
    new_record = pd.DataFrame({'ID': [student_id], 'Name': [student_name], 'Time': [time_str], 'Date': [date_str]})
    new_record.to_csv(ATTENDANCE_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')

# ==========================================
# تهيئة البيانات وبناء الواجهة
# ==========================================
init_attendance_file()
df_students, students_dict = load_students_data()

# الإحصائيات التي كانت تظهر لك 0 أصبحت الآن تقرأ من الملف الصحيح
total_students = len(df_students) if not df_students.empty else 0
attended_today_set = get_attended_today()
total_attended = len(attended_today_set)
total_absent = total_students - total_attended if total_students > 0 else 0

st.title("🎓 نظام رَصْد - تسجيل الحضور والغياب")

# --- الشريط الجانبي ---
st.sidebar.header("⚙️ إعدادات الكاميرا")
camera_url = st.sidebar.text_input("رابط الكاميرا:", value="http://192.168.1.5:8080/shot.jpg")
run = st.sidebar.checkbox('تشغيل الكاميرا لبدء المسح 📷')

st.sidebar.markdown("---")
st.sidebar.header("📊 إحصائيات اليوم")
st.sidebar.metric(label="إجمالي الطلاب المسجلين", value=total_students)
st.sidebar.metric(label="🟢 عدد الحاضرين", value=total_attended)
st.sidebar.metric(label="🔴 عدد الغائبين", value=total_absent)

# --- تقسيم الشاشة ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📷 شاشة المسح الحي")
    frame_window = st.image([])
    status_text = st.empty()

with col2:
    st.subheader("📝 آخر من سجلوا الحضور")
    records_placeholder = st.empty()
    
    def update_records_display():
        if os.path.exists(ATTENDANCE_FILE):
            try:
                df_att = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
                today = datetime.now().strftime('%Y-%m-%d')
                today_att = df_att[df_att['Date'] == today]
                if not today_att.empty:
                    display_df = today_att.tail(10)[['Name', 'Time']].iloc[::-1]
                    display_df.columns = ['الاسم', 'وقت الحضور']
                    records_placeholder.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    records_placeholder.info("لم يسجل أحد حضوره اليوم بعد.")
            except:
                pass
    
    update_records_display()

# ==========================================
# تشغيل الكاميرا وقراءة الباركود
# ==========================================
if run:
    status_text.info("⏳ جاري الاتصال بالكاميرا...")
    while run:
        try:
            imgResp = urllib.request.urlopen(camera_url, timeout=5)
            imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
            img = cv2.imdecode(imgNp, -1)
            
            for barcode in decode(img):
                student_id = barcode.data.decode('utf-8').strip()
                
                # رسم المربع
                pts = np.array([barcode.polygon], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(img, [pts], True, (0, 255, 0), 3)
                
                # التحقق والتسجيل
                if student_id not in attended_today_set:
                    # جلب اسم الطالب من القاموس
                    student_name = students_dict.get(student_id, student_id)
                    mark_attendance(student_id, student_name)
                    attended_today_set.add(student_id)
                    
                    status_text.success(f"✅ تم تسجيل حضور: {student_name}")
                    update_records_display()
                else:
                    student_name = students_dict.get(student_id, student_id)
                    status_text.warning(f"⚠️ {student_name} مسجل مسبقاً اليوم!")
                    
            # عرض الصورة في المتصفح
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame_window.image(img_rgb)
            
        except Exception as e:
            status_text.error(f"❌ حدث خطأ في الاتصال بالكاميرا: {e}")
            break
else:
    status_text.info("الكاميرا متوقفة. قم بتفعيلها من الشريط الجانبي لبدء تسجيل الحضور.")
    black_img = np.zeros((480, 640, 3), dtype=np.uint8)
    frame_window.image(black_img)
