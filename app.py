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
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['الاسم/الرقم', 'التاريخ والوقت', 'الحالة'])
        df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')

def load_students():
    if os.path.exists(STUDENTS_FILE):
        try:
            df = pd.read_excel(STUDENTS_FILE)
            df.columns = df.columns.str.strip().str.lower()
            barcode_col = None
            for col in ['barcode', 'id', 'رقم', 'كود', 'code', 'student_id']:
                if col in df.columns:
                    barcode_col = col
                    break
            name_col = None
            for col in ['name', 'اسم', 'الاسم', 'student_name', 'اسم الطالب']:
                if col in df.columns:
                    name_col = col
                    break
            if barcode_col is None and len(df.columns) >= 1:
                barcode_col = df.columns[0]
            if name_col is None and len(df.columns) >= 2:
                name_col = df.columns[1]
            if barcode_col and name_col:
                students = dict(
                    zip(
                        df[barcode_col].astype(str).str.strip(),
                        df[name_col].astype(str).str.strip()
                    )
                )
                return students, df
        except Exception as e:
            st.sidebar.error(f"❌ خطأ في قراءة الملف: {e}")
    return {}, pd.DataFrame()

def get_attended_today():
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
    identifier_str = str(identifier).strip()
    
    # [تعديل هام] التحقق من أن الباركود ينتمي لقائمة الطلاب
    if identifier_str not in students_dict:
        return False, identifier_str, "باركود خارجي غير مسجل في قائمة الطلاب ❌"
        
    name = students_dict[identifier_str]
    
    if identifier in st.session_state.scanned_session:
        return False, name, "مسجّل مسبقاً في هذه الجلسة ✋"
    if name in get_attended_today():
        st.session_state.scanned_session.add(identifier)
        return False, name, "مسجّل مسبقاً اليوم 📅"
    try:
        dt_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = pd.DataFrame({
            'الاسم/الرقم' : [name],
            'التاريخ والوقت': [dt_string],
            'الحالة' : ['حاضر']
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
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    results = []
    for barcode in decode(img_gray):
        data = barcode.data.decode('utf-8')
        results.append((data, barcode.type))
    return results

def draw_on_image(image):
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
    # ══════════════════════════════════════════════════════
    # ✅ الإعداد الأساسي للصفحة
    # ══════════════════════════════════════════════════════
    st.set_page_config(
        page_title="نظام رَصْد للحضور",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ══════════════════════════════════════════════════════
    # ✅ CSS آمن لا يكسر تخطيط Streamlit
    # ══════════════════════════════════════════════════════
    st.markdown("""
    <style>
    /* ── المحتوى الرئيسي RTL ── */
    .block-container { direction: rtl; }
    /* ── النصوص فقط بدون المساس بـ div/span ── */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { text-align: right !important; }
    /* ── الجداول ── */
    [data-testid="stDataFrame"] { direction: rtl !important; }
    /* ── مدخلات النصوص ── */
    input { direction: rtl !important; text-align: right !important; }
    /* ── الشريط الجانبي ── */
    [data-testid="stSidebar"] { direction: rtl; min-width: 280px; max-width: 320px; }
    [data-testid="stSidebar"] .block-container { padding-top: 1rem; }
    /* ── ألوان الشريط الجانبي ── */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1a3c6e 0%, #0d2444 100%); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    /* ── بطاقات المعلومات ── */
    .info-card {
        background: linear-gradient(135deg, #1a3c6e, #2563eb);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.4rem 0;
    }
    /* ── بطاقة الحاضر ── */
    .present-card {
        background: #e8f5e9;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border-right: 4px solid #4caf50;
        text-align: right;
    }
    /* ── بطاقة الغائب ── */
    .absent-card {
        background: #ffebee;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border-right: 4px solid #f44336;
        text-align: right;
    }
    /* ── الأزرار ── */
    .stButton > button { border-radius: 8px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # تهيئة حالة الجلسة والملفات
    # ══════════════════════════════════════════════════════
    if 'scanned_session' not in st.session_state:
        st.session_state.scanned_session = set()
    initialize_file()
    students_dict, students_df = load_students()

    # ══════════════════════════════════════════════════════
    # ✅ الشريط الجانبي
    # ══════════════════════════════════════════════════════
    with st.sidebar:
        # عنوان الشريط
        st.markdown("## 🎓 نظام رَصْد")
        st.markdown("---")

        # إحصائيات سريعة
        today_count = len(get_attended_today())
        session_count = len(st.session_state.scanned_session)
        total_count = len(students_dict)
        st.markdown("### 📊 إحصائيات")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("الجلسة", session_count)
            st.metric("الطلاب", total_count)
        with col_b:
            st.metric("اليوم", today_count)
            absent_count = total_count - today_count if total_count > 0 else 0
            st.metric("الغائبون", absent_count)
        st.markdown("---")

        # رفع ملف الطلاب
        st.markdown("### 📤 ملف الطلاب")
        st.caption("أعمدة مطلوبة: barcode, name")
        uploaded_students = st.file_uploader(
            "اختر ملف Excel",
            type=['xlsx', 'xls'],
            key='students_upload'
        )
        if uploaded_students:
            with open(STUDENTS_FILE, 'wb') as f:
                f.write(uploaded_students.getbuffer())
            st.success("✅ تم رفع الملف!")
            st.rerun()

        # حالة الملف
        if students_dict:
            st.success(f"✅ {len(students_dict)} طالب محمّل")
        else:
            st.error("❌ لا توجد بيانات طلاب")
        st.markdown("---")

        # أزرار التحكم
        st.markdown("### ⚙️ التحكم")
        if st.button("🔄 إعادة تعيين الجلسة"):
            st.session_state.scanned_session = set()
            st.success("✅ تم!")
            st.rerun()
        if st.button("🗑️ مسح سجل اليوم"):
            if os.path.exists(ATTENDANCE_FILE):
                today = datetime.now().strftime('%Y-%m-%d')
                df_all = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
                df_all['date'] = pd.to_datetime(
                    df_all['التاريخ والوقت'], errors='coerce'
                ).dt.strftime('%Y-%m-%d')
                df_keep = df_all[df_all['date'] != today].drop(columns=['date'])
                df_keep.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')
                st.session_state.scanned_session = set()
                st.success("✅ تم المسح!")
                st.rerun()
        st.markdown("---")
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # ══════════════════════════════════════════════════════
    # العنوان الرئيسي
    # ══════════════════════════════════════════════════════
    st.markdown("<h1>🎓 نظام رَصْد للحضور</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # ══════════════════════════════════════════════════════
    # التبويبات
    # ══════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "📷 تسجيل الحضور",
        "👥 قائمة الطلاب",
        "📊 سجل الحضور",
        "📋 تقرير اليوم"
    ])

    # ══════════════════════════════════════════════════════
    # TAB 1: تسجيل الحضور
    # ══════════════════════════════════════════════════════
    with tab1:
        st.header("📷 تسجيل الحضور")
        if not students_dict:
            st.warning("⚠️ يرجى رفع ملف الطلاب من الشريط الجانبي أولاً")

        method = st.radio(
            "اختر طريقة الإدخال:",
            ["📁 رفع صورة", "📷 كاميرا المتصفح", "⌨️ إدخال يدوي"],
            horizontal=True
        )
        st.markdown("---")

        # ── رفع صورة ──────────────────────────────────
        if "رفع صورة" in method:
            col1, col2 = st.columns(2)
            with col1:
                uploaded_file = st.file_uploader(
                    "ارفع صورة الباركود أو QR",
                    type=['jpg', 'jpeg', 'png', 'bmp'],
                    key='barcode_image'
                )
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(
                        image,
                        caption="الصورة المرفوعة",
                        use_column_width=True
                    )
            if uploaded_file:
                barcodes = scan_barcodes(image)
                with col2:
                    st.subheader("نتائج المسح:")
                    if barcodes:
                        st.success(f"🔍 تم اكتشاف {len(barcodes)} باركود")
                        for data, btype in barcodes:
                            success, name, message = mark_attendance(
                                data, students_dict
                            )
                            if success:
                                st.success(
                                    f"✅ **{name}**\n"
                                    f"- الكود: {data}\n"
                                    f"- {message}"
                                )
                                st.balloons()
                            else:
                                st.warning(
                                    f"⚠️ **{name}**\n"
                                    f"- {message}"
                                )
                        annotated = draw_on_image(image)
                        st.image(
                            annotated,
                            caption="الباركود المكتشف",
                            use_column_width=True
                        )
                    else:
                        st.error("❌ لم يتم اكتشاف أي باركود")
                        st.info("💡 تأكد من وضوح الصورة")

        # ── كاميرا المتصفح ─────────────────────────────
        elif "كاميرا" in method:
            col1, col2 = st.columns(2)
            with col1:
                camera_image = st.camera_input("📷 التقط صورة الباركود")
                if camera_image:
                    image = Image.open(camera_image)
                    barcodes = scan_barcodes(image)
            if camera_image:
                with col2:
                    st.subheader("نتائج المسح:")
                    if barcodes:
                        for data, btype in barcodes:
                            success, name, message = mark_attendance(
                                data, students_dict
                            )
                            if success:
                                st.success(f"✅ **{name}** - {data}")
                                st.balloons()
                            else:
                                st.warning(f"⚠️ {name}: {message}")
                    else:
                        st.error("❌ لم يتم اكتشاف باركود")

        # ── إدخال يدوي ────────────────────────────────
        elif "يدوي" in method:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("⌨️ الإدخال اليدوي")
                with st.form("manual_form", clear_on_submit=True):
                    manual_input = st.text_input(
                        "أدخل رقم الباركود:",
                        placeholder="مثال: S001"
                    )
                    if manual_input.strip():
                        preview = students_dict.get(
                            manual_input.strip(), "غير موجود في القائمة ⚠️"
                        )
                        st.info(f"👤 الطالب: **{preview}**")
                    submitted = st.form_submit_button(
                        "✅ تسجيل الحضور", use_container_width=True
                    )
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
    # TAB 2: قائمة الطلاب
    # ══════════════════════════════════════════════════════
    with tab2:
        st.header("👥 قائمة الطلاب")
        if not students_dict:
            st.error("❌ لا توجد بيانات طلاب")
            st.markdown("""
            ### كيفية إضافة الطلاب:
            1. افتح Excel وأنشئ جدولاً بعمودين:
               - عمود `barcode` ← رقم الباركود
               - عمود `name` ← اسم الطالب
            2. احفظ الملف بصيغة `.xlsx`
            3. ارفعه من الشريط الجانبي
            """)
            # ملف نموذجي للتحميل
            sample = pd.DataFrame({
                'barcode': ['S001','S002','S003','S004','S005'],
                'name' : [ 'أحمد محمد', 'فاطمة علي', 'محمد سالم', 'نورة خالد', 'عمر سعيد' ],
                'class': [ 'الصف الأول', 'الصف الأول', 'الصف الثاني', 'الصف الثاني', 'الصف الثالث' ]
            })
            st.download_button(
                label="⬇️ تحميل ملف نموذجي",
                data=sample.to_csv(index=False).encode('utf-8-sig'),
                file_name="students_sample.csv",
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.success(f"✅ إجمالي الطلاب: **{len(students_dict)}**")
            search_student = st.text_input(
                "🔍 بحث عن طالب:",
                placeholder="اكتب الاسم أو الرقم..."
            )
            display_df = pd.DataFrame(
                list(students_dict.items()),
                columns=['رقم الباركود', 'اسم الطالب']
            )
            display_df.index = range(1, len(display_df) + 1)
            if search_student:
                mask = (
                    display_df['اسم الطالب'].str.contains(
                        search_student, na=False
                    ) |
                    display_df['رقم الباركود'].str.contains(
                        search_student, na=False
                    )
                )
                display_df = display_df[mask]
            st.dataframe(display_df, use_container_width=True, height=400)
            if not students_df.empty:
                with st.expander("📄 عرض بيانات الملف الكاملة"):
                    st.dataframe(students_df, use_container_width=True)

    # ══════════════════════════════════════════════════════
    # TAB 3: سجل الحضور
    # ══════════════════════════════════════════════════════
    with tab3:
        st.header("📊 سجل الحضور الكامل")
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
            if not df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    search = st.text_input(
                        "🔍 بحث بالاسم:",
                        placeholder="اكتب الاسم..."
                    )
                with col2:
                    date_filter = st.date_input(
                        "📅 فلترة بالتاريخ:",
                        value=None
                    )
                filtered_df = df.copy()
                if search:
                    filtered_df = filtered_df[
                        filtered_df['الاسم/الرقم'].str.contains(
                            search, na=False
                        )
                    ]
                if date_filter:
                    filtered_df['date'] = pd.to_datetime(
                        filtered_df['التاريخ والوقت'], errors='coerce'
                    ).dt.date
                    filtered_df = filtered_df[
                        filtered_df['date'] == date_filter
                    ]
                    filtered_df = filtered_df.drop(columns=['date'])
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )
                st.info(f"📌 إجمالي السجلات: **{len(filtered_df)}**")
                st.download_button(
                    label="⬇️ تحميل ملف CSV",
                    data=filtered_df.to_csv(
                        index=False, encoding='utf-8-sig'
                    ).encode('utf-8-sig'),
                    file_name=f"attendance_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
            else:
                st.info("📭 لا توجد سجلات بعد")
        else:
            st.warning("⚠️ ملف الحضور غير موجود")

    # ══════════════════════════════════════════════════════
    # TAB 4: تقرير اليوم
    # ══════════════════════════════════════════════════════
    with tab4:
        st.header(f"📋 تقرير {datetime.now().strftime('%Y-%m-%d')}")
        today_names = get_attended_today()
        total = len(students_dict)
        present = len(today_names)
        absent_count = total - present if total > 0 else 0

        # بطاقات الإحصائيات
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ حاضر اليوم", present)
        col2.metric("🎓 إجمالي الطلاب", total)
        col3.metric("❌ غائب", absent_count)
        st.markdown("---")

        col1, col2 = st.columns(2)
        # قائمة الحاضرين
        with col1:
            st.subheader("✅ الحاضرون")
            if today_names:
                for i, name in enumerate(sorted(today_names), 1):
                    st.markdown(
                        f"<div class='present-card'>{i}. {name}</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.info("📭 لا يوجد حضور بعد")
        # قائمة الغائبين
        with col2:
            st.subheader("❌ الغائبون")
            if students_dict:
                absent_names = set(students_dict.values()) - set(today_names)
                if absent_names:
                    for i, name in enumerate(sorted(absent_names), 1):
                        st.markdown(
                            f"<div class='absent-card'>{i}. {name}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.success("🎉 جميع الطلاب حاضرون!")
            else:
                st.info("لا توجد بيانات طلاب")

# ============================================================
# ▶️ تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    main()
