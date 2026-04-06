# app.py - نسخة Streamlit كاملة
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np
import cv2

# ============================================================
# ⚙️ الإعدادات
# ============================================================
ATTENDANCE_FILE = 'attendance.csv'
STUDENTS_FILE = 'students.xlsx'

# ============================================================
# 🔧 دوال مساعدة
# ============================================================
def initialize_file():
    """إنشاء ملف الحضور إن لم يكن موجوداً"""
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['الاسم/الرقم', 'التاريخ والوقت', 'الحالة'])
        df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')

def load_students():
    """تحميل بيانات الطلاب من Excel"""
    if os.path.exists(STUDENTS_FILE):
        try:
            df = pd.read_excel(STUDENTS_FILE)
            if 'barcode' in df.columns and 'name' in df.columns:
                return dict(zip(df['barcode'].astype(str), df['name'].astype(str)))
        except Exception as e:
            st.warning(f"⚠️ خطأ في قراءة ملف الطلاب: {e}")
    return {}

def get_attended_today():
    """جلب من سجّل حضوره اليوم"""
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
            if not df.empty and 'التاريخ والوقت' in df.columns:
                df['date'] = pd.to_datetime(
                    df['التاريخ والوقت'], errors='coerce'
                ).dt.strftime('%Y-%m-%d')
                return set(df[df['date'] == today]['الاسم/الرقم'].tolist())
    except Exception:
        pass
    return set()

def mark_attendance(identifier, students_dict):
    """
    تسجيل الحضور
    يُرجع: (نجح, الاسم, الرسالة)
    """
    name = students_dict.get(str(identifier), str(identifier))
    # التحقق من التكرار في الجلسة
    if identifier in st.session_state.scanned_session:
        return False, name, "مسجّل مسبقاً في هذه الجلسة ✋"
    # التحقق من التكرار في اليوم
    if name in get_attended_today():
        st.session_state.scanned_session.add(identifier)
        return False, name, "مسجّل مسبقاً اليوم 📅"
    # الحفظ في الملف
    try:
        dt_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = pd.DataFrame({
            'الاسم/الرقم': [name],
            'التاريخ والوقت': [dt_string],
            'الحالة': ['حاضر']
        })
        new_row.to_csv(
            ATTENDANCE_FILE,
            mode='a',
            header=False,
            index=False,
            encoding='utf-8-sig'
        )
        st.session_state.scanned_session.add(identifier)
        return True, name, f"✅ تم التسجيل - {dt_string}"
    except Exception as e:
        return False, name, f"❌ خطأ: {e}"

def scan_barcodes(image):
    """
    قراءة الباركود/QR من الصورة
    يُرجع: قائمة من (البيانات, النوع)
    """
    img_array = np.array(image)
    # تحويل RGB إلى BGR لـ OpenCV
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    results = []
    for barcode in decode(img_gray):
        data = barcode.data.decode('utf-8')
        results.append((data, barcode.type))
    return results

def draw_on_image(image, barcodes_info):
    """رسم مستطيلات حول الباركود في الصورة"""
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    for barcode in decode(img_bgr):
        pts = np.array([barcode.polygon], np.int32).reshape((-1, 1, 2))
        cv2.polylines(img_bgr, [pts], True, (0, 255, 0), 3)
        rect = barcode.rect
        cv2.putText(
            img_bgr,
            barcode.data.decode('utf-8'),
            (rect[0], rect[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

# ============================================================
# 🚀 واجهة Streamlit
# ============================================================
def main():
    st.set_page_config(
        page_title="نظام الحضور",
        page_icon="🎓",
        layout="wide"
    )

    # ── CSS للغة العربية ──────────────────────────────────
    st.markdown("""
    <style>
    body { direction: rtl; }
    .main { direction: rtl; text-align: right; }
    .stAlert { direction: rtl; }
    h1, h2, h3 { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

    # ── تهيئة حالة الجلسة ─────────────────────────────────
    if 'scanned_session' not in st.session_state:
        st.session_state.scanned_session = set()

    # ── تهيئة الملفات ─────────────────────────────────────
    initialize_file()
    students_dict = load_students()

    # ── العنوان ───────────────────────────────────────────
    st.title("🎓 نظام تسجيل الحضور بالباركود")
    st.markdown("---")

    # ============================================================
    # 📌 Sidebar - الشريط الجانبي
    # ============================================================
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        st.info(f"""
        📊 **إحصائيات سريعة**
        - 👥 الجلسة الحالية: **{len(st.session_state.scanned_session)}**
        - 📅 اليوم: **{len(get_attended_today())}**
        """)
        st.markdown("---")

        # رفع ملف الطلاب
        st.subheader("📤 رفع بيانات الطلاب")
        uploaded_students = st.file_uploader(
            "ملف Excel (barcode, name)",
            type=['xlsx', 'xls'],
            key='students_upload'
        )
        if uploaded_students:
            with open(STUDENTS_FILE, 'wb') as f:
                f.write(uploaded_students.getbuffer())
            st.success("✅ تم رفع ملف الطلاب")
            st.rerun()

        st.markdown("---")

        # إعادة تعيين الجلسة
        if st.button("🔄 إعادة تعيين الجلسة", use_container_width=True):
            st.session_state.scanned_session = set()
            st.success("✅ تم إعادة التعيين")

    # ============================================================
    # 📑 التبويبات
    # ============================================================
    tab1, tab2, tab3 = st.tabs([
        "📷 تسجيل الحضور",
        "📊 سجل الحضور",
        "📋 تقرير اليوم"
    ])

    # ══════════════════════════════════════════════════════
    # TAB 1: تسجيل الحضور
    # ══════════════════════════════════════════════════════
    with tab1:
        st.header("📷 تسجيل الحضور")
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📸 رفع صورة")
            method = st.radio(
                "اختر طريقة الإدخال:",
                ["📁 رفع صورة", "📷 كاميرا المتصفح", "⌨️ إدخال يدوي"],
                horizontal=True
            )

        # ── طريقة 1: رفع صورة ─────────────────────────────
        if "رفع صورة" in method:
            uploaded_file = st.file_uploader(
                "ارفع صورة تحتوي على باركود أو QR كود",
                type=['jpg', 'jpeg', 'png', 'bmp'],
                key='barcode_image'
            )
            if uploaded_file:
                image = Image.open(uploaded_file)
                with col1:
                    st.image(image, caption="الصورة المرفوعة", use_column_width=True)

                # فحص الباركود
                barcodes = scan_barcodes(image)

                with col2:
                    if barcodes:
                        st.success(f"🔍 تم اكتشاف {len(barcodes)} باركود")
                        for data, btype in barcodes:
                            success, name, message = mark_attendance(data, students_dict)
                            if success:
                                st.success(f"""
                                ✅ **تم تسجيل الحضور**
                                - 👤 الاسم: **{name}**
                                - 🔖 النوع: {btype}
                                - ⏰ {message}
                                """)
                                st.balloons()
                            else:
                                st.warning(f"""
                                ⚠️ **{name}**
                                - {message}
                                """)
                        # عرض الصورة مع التوضيحات
                        annotated = draw_on_image(image, barcodes)
                        st.image(annotated, caption="الصورة مع الباركود", use_column_width=True)
                    else:
                        st.error("❌ لم يتم اكتشاف أي باركود في الصورة")
                        st.info("💡 تأكد من وضوح الصورة وأن الباركود مرئي بالكامل")

        # ── طريقة 2: كاميرا المتصفح ───────────────────────
        elif "كاميرا" in method:
            camera_image = st.camera_input("📷 التقط صورة الباركود")
            if camera_image:
                image = Image.open(camera_image)
                barcodes = scan_barcodes(image)
                if barcodes:
                    for data, btype in barcodes:
                        success, name, message = mark_attendance(data, students_dict)
                        if success:
                            st.success(f"✅ تم تسجيل: **{name}**")
                            st.balloons()
                        else:
                            st.warning(f"⚠️ {name}: {message}")
                else:
                    st.error("❌ لم يتم اكتشاف باركود - حاول مرة أخرى")

        # ── طريقة 3: إدخال يدوي ───────────────────────────
        elif "يدوي" in method:
            with st.form("manual_form"):
                manual_input = st.text_input(
                    "أدخل رقم الطالب أو الاسم:",
                    placeholder="مثال: 12345"
                )
                submitted = st.form_submit_button("✅ تسجيل", use_container_width=True)
                if submitted and manual_input.strip():
                    success, name, message = mark_attendance(
                        manual_input.strip(), students_dict
                    )
                    if success:
                        st.success(f"✅ تم تسجيل: **{name}**")
                        st.balloons()
                    else:
                        st.warning(f"⚠️ {name}: {message}")

    # ══════════════════════════════════════════════════════
    # TAB 2: سجل الحضور الكامل
    # ══════════════════════════════════════════════════════
    with tab2:
        st.header("📊 سجل الحضور الكامل")
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
            if not df.empty:
                # فلاتر البحث
                col1, col2 = st.columns(2)
                with col1:
                    search = st.text_input("🔍 بحث بالاسم:", placeholder="اكتب الاسم...")
                with col2:
                    date_filter = st.date_input("📅 فلترة بالتاريخ:", value=None)

                # تطبيق الفلاتر
                filtered_df = df.copy()
                if search:
                    filtered_df = filtered_df[
                        filtered_df['الاسم/الرقم'].str.contains(search, na=False)
                    ]
                if date_filter:
                    filtered_df['date'] = pd.to_datetime(
                        filtered_df['التاريخ والوقت'], errors='coerce'
                    ).dt.date
                    filtered_df = filtered_df[filtered_df['date'] == date_filter]
                    filtered_df = filtered_df.drop(columns=['date'])

                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )
                st.info(f"📌 إجمالي السجلات: **{len(filtered_df)}**")

                # تحميل الملف
                st.download_button(
                    label="⬇️ تحميل ملف CSV",
                    data=filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                    file_name=f"attendance_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
            else:
                st.info("📭 لا توجد سجلات بعد")
        else:
            st.warning("⚠️ ملف الحضور غير موجود")

    # ══════════════════════════════════════════════════════
    # TAB 3: تقرير اليوم
    # ══════════════════════════════════════════════════════
    with tab3:
        st.header(f"📋 تقرير يوم {datetime.now().strftime('%Y-%m-%d')}")
        today_names = get_attended_today()

        col1, col2, col3 = st.columns(3)
        col1.metric("✅ حاضر اليوم", len(today_names))
        col2.metric("🎓 إجمالي الطلاب", len(students_dict) if students_dict else "—")
        col3.metric("📌 الجلسة الحالية", len(st.session_state.scanned_session))

        if today_names:
            st.subheader("👥 الحاضرون اليوم:")
            for i, name in enumerate(sorted(today_names), 1):
                st.write(f"{i}. {name}")
        else:
            st.info("📭 لا يوجد تسجيلات اليوم بعد")

# ============================================================
# ▶️ تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    main()
