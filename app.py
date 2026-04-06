# app.py - نسخة Streamlit كاملة مصححة
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
    """ ✅ الإصلاح الثاني: تحميل بيانات الطلاب بشكل صحيح
        يقرأ أي أعمدة موجودة في الملف """
    if os.path.exists(STUDENTS_FILE):
        try:
            df = pd.read_excel(STUDENTS_FILE)
            # ── تنظيف أسماء الأعمدة ──────────────────────
            df.columns = df.columns.str.strip().str.lower()
            st.sidebar.caption(f"📋 أعمدة الملف: {list(df.columns)}")

            # ── البحث عن عمود الباركود ───────────────────
            barcode_col = None
            for col in ['barcode', 'id', 'رقم', 'كود', 'code', 'student_id']:
                if col in df.columns:
                    barcode_col = col
                    break

            # ── البحث عن عمود الاسم ──────────────────────
            name_col = None
            for col in ['name', 'اسم', 'الاسم', 'student_name', 'اسم الطالب']:
                if col in df.columns:
                    name_col = col
                    break

            # ── إذا لم يجد الأعمدة استخدم أول عمودين ────
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
                return students, df  # ← إرجاع القاموس والـ DataFrame
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
    name = students_dict.get(str(identifier).strip(), str(identifier).strip())
    if identifier in st.session_state.scanned_session:
        return False, name, "مسجّل مسبقاً في هذه الجلسة ✋"
    if name in get_attended_today():
        st.session_state.scanned_session.add(identifier)
        return False, name, "مسجّل مسبقاً اليوم 📅"
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
    # ✅ الإصلاح الأول: initial_sidebar_state="expanded"
    st.set_page_config(
        page_title="نظام الحضور",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"  # ← يفتح الشريط دائماً
    )

    # ✅ الإصلاح الأول: CSS لنقل الشريط لليسار وتثبيته
    st.markdown("""
    <style>
    /* ── اتجاه الصفحة ── */
    body, .main, [data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
    }
    /* ✅ إصلاح الشريط الجانبي - نقله لليسار */
    [data-testid="stSidebar"] {
        right: auto !important;
        left: 0 !important;
        direction: rtl;
    }
    /* ✅ إصلاح زر فتح/إغلاق الشريط */
    [data-testid="collapsedControl"] {
        right: auto !important;
        left: 0 !important;
    }
    /* ── محتوى الشريط الجانبي ── */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #1a3c6e 0%, #0d2444 100%);
        padding-top: 2rem;
    }
    /* ── نصوص الشريط الجانبي ── */
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: white !important;
        text-align: right !important;
    }
    /* ── العنوان الرئيسي ── */
    h1 {
        text-align: center;
        color: #1a3c6e;
    }
    h2, h3 {
        text-align: right;
    }
    /* ── بطاقات المعلومات ── */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    /* ── تنسيق الجداول ── */
    .dataframe {
        direction: rtl;
        text-align: right;
    }
    /* ── الأزرار ── */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        background: #1a3c6e;
        color: white;
        border: none;
        padding: 0.5rem;
    }
    .stButton button:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }
    /* ── التبويبات ── */
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── تهيئة حالة الجلسة ─────────────────────────────
    if 'scanned_session' not in st.session_state:
        st.session_state.scanned_session = set()

    # ── تهيئة الملفات ─────────────────────────────────
    initialize_file()
    # ✅ الإصلاح الثاني: تحميل بيانات الطلاب مع DataFrame
    students_dict, students_df = load_students()

    # ── العنوان ───────────────────────────────────────
    st.markdown("""
    <h1>🎓 نظام تسجيل الحضور بالباركود</h1>
    <p style='text-align:center; color:#666;'> مدرسة النجاح - نظام الحضور الذكي </p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ============================================================
    # ✅ الشريط الجانبي المُصلح - يفتح على اليسار
    # ============================================================
    with st.sidebar:
        # ── شعار وعنوان ───────────────────────────────
        st.markdown("""
        <div style='text-align:center; padding:1rem 0;'>
            <h1 style='color:white; font-size:2rem;'>🎓</h1>
            <h3 style='color:white;'>نظام الحضور</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # ── إحصائيات سريعة ────────────────────────────
        today_count = len(get_attended_today())
        session_count = len(st.session_state.scanned_session)
        st.markdown(f"""
        <div class='info-card'>
            <h4 style='margin:0; color:white;'>📊 إحصائيات سريعة</h4>
            <hr style='border-color:rgba(255,255,255,0.3);'>
            <p style='margin:0.3rem 0; color:white;'> 👥 الجلسة الحالية: <b>{session_count}</b> </p>
            <p style='margin:0.3rem 0; color:white;'> 📅 حضور اليوم: <b>{today_count}</b> </p>
            <p style='margin:0.3rem 0; color:white;'> 🎓 إجمالي الطلاب: <b>{len(students_dict)}</b> </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # ✅ رفع ملف الطلاب مع معاينة
        st.markdown("### 📤 رفع بيانات الطلاب")
        st.caption("الأعمدة المطلوبة: barcode, name")
        uploaded_students = st.file_uploader(
            "اختر ملف Excel:",
            type=['xlsx', 'xls'],
            key='students_upload'
        )
        if uploaded_students:
            with open(STUDENTS_FILE, 'wb') as f:
                f.write(uploaded_students.getbuffer())
            st.success("✅ تم رفع الملف بنجاح!")
            st.rerun()

        # ✅ عرض حالة الملف
        if students_dict:
            st.success(f"✅ {len(students_dict)} طالب محمّل")
        else:
            st.error("❌ لا توجد بيانات طلاب")
            st.info("""
            **كيفية إعداد ملف Excel:**
            - عمود `barcode` ← رقم الباركود
            - عمود `name` ← اسم الطالب
            """)
        st.markdown("---")

        # ── أزرار التحكم ──────────────────────────────
        st.markdown("### ⚙️ التحكم")
        if st.button("🔄 إعادة تعيين الجلسة", use_container_width=True):
            st.session_state.scanned_session = set()
            st.success("✅ تم إعادة التعيين")
            st.rerun()
        if st.button("🗑️ مسح سجل اليوم", use_container_width=True):
            if os.path.exists(ATTENDANCE_FILE):
                today = datetime.now().strftime('%Y-%m-%d')
                df_all = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
                df_all['date'] = pd.to_datetime(
                    df_all['التاريخ والوقت'], errors='coerce'
                ).dt.strftime('%Y-%m-%d')
                df_keep = df_all[df_all['date'] != today].drop(columns=['date'])
                df_keep.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')
                st.session_state.scanned_session = set()
                st.success("✅ تم مسح سجل اليوم")
                st.rerun()
        st.markdown("---")
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # ============================================================
    # 📑 التبويبات الرئيسية
    # ============================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📷 تسجيل الحضور",
        "👥 قائمة الطلاب",
        "📊 سجل الحضور",
        "📋 تقرير اليوم"
    ])

    # ══════════════════════════════════════════════════════════
    # TAB 1: تسجيل الحضور
    # ══════════════════════════════════════════════════════════
    with tab1:
        st.header("📷 تسجيل الحضور")
        # تحذير إذا لم توجد بيانات طلاب
        if not students_dict:
            st.warning("""
            ⚠️ **لا توجد بيانات طلاب!**
            يرجى رفع ملف Excel من الشريط الجانبي يحتوي على عمودي `barcode` و `name`
            """)

        method = st.radio(
            "اختر طريقة الإدخال:",
            ["📁 رفع صورة", "📷 كاميرا المتصفح", "⌨️ إدخال يدوي"],
            horizontal=True
        )
        st.markdown("---")

        # ── طريقة 1: رفع صورة ─────────────────────────
        if "رفع صورة" in method:
            col1, col2 = st.columns([1, 1])
            with col1:
                uploaded_file = st.file_uploader(
                    "ارفع صورة تحتوي على باركود أو QR كود",
                    type=['jpg', 'jpeg', 'png', 'bmp'],
                    key='barcode_image'
                )
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="الصورة المرفوعة", use_column_width=True)

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
                                st.success(f"""
                                ✅ **تم تسجيل الحضور**
                                - 👤 الاسم: **{name}**
                                - 🔖 النوع: {btype}
                                - 🔢 الكود: {data}
                                - ⏰ {message}
                                """)
                                st.balloons()
                            else:
                                st.warning(f"""
                                ⚠️ **{name}**
                                - {message}
                                - 🔢 الكود: {data}
                                """)
                        annotated = draw_on_image(image)
                        st.image(
                            annotated,
                            caption="الصورة مع الباركود المكتشف",
                            use_column_width=True
                        )
                    else:
                        st.error("❌ لم يتم اكتشاف أي باركود")
                        st.info("💡 تأكد من وضوح الصورة وأن الباركود مرئي بالكامل")

        # ── طريقة 2: كاميرا المتصفح ───────────────────
        elif "كاميرا" in method:
            col1, col2 = st.columns([1, 1])
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
                                st.success(f"""
                                ✅ **تم تسجيل: {name}**
                                - 🔢 الكود: {data}
                                """)
                                st.balloons()
                            else:
                                st.warning(f"⚠️ {name}: {message}")
                    else:
                        st.error("❌ لم يتم اكتشاف باركود")

        # ── طريقة 3: إدخال يدوي ───────────────────────
        elif "يدوي" in method:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("⌨️ الإدخال اليدوي")
                with st.form("manual_form", clear_on_submit=True):
                    manual_input = st.text_input(
                        "أدخل رقم الباركود:",
                        placeholder="مثال: S001"
                    )
                    # ✅ عرض اسم الطالب أثناء الكتابة
                    if manual_input.strip():
                        preview_name = students_dict.get(
                            manual_input.strip(), "غير موجود في القائمة"
                        )
                        st.info(f"👤 الطالب: **{preview_name}**")
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

    # ══════════════════════════════════════════════════════════
    # ✅ TAB 2: قائمة الطلاب (جديد)
    # ══════════════════════════════════════════════════════════
    with tab2:
        st.header("👥 قائمة الطلاب")
        if not students_dict:
            st.error("❌ لا توجد بيانات طلاب")
            st.markdown("""
            ### كيفية إضافة الطلاب:
            1. افتح Excel وأنشئ جدول بعمودين:
               - عمود `barcode` ← رقم الباركود
               - عمود `name` ← اسم الطالب
            2. احفظ الملف بصيغة `.xlsx`
            3. ارفعه من الشريط الجانبي
            """)
            # ✅ زر تحميل ملف نموذجي
            sample_data = pd.DataFrame({
                'barcode': ['S001', 'S002', 'S003', 'S004', 'S005'],
                'name': ['أحمد محمد', 'فاطمة علي', 'محمد سالم', 'نورة خالد', 'عمر سعيد'],
                'class': ['الصف الأول', 'الصف الأول', 'الصف الثاني', 'الصف الثاني', 'الصف الثالث']
            })
            st.download_button(
                label="⬇️ تحميل ملف نموذجي",
                data=sample_data.to_csv(index=False).encode('utf-8-sig'),
                file_name="students_sample.csv",
                mime='text/csv',
                use_container_width=True
            )
        else:
            # ✅ عرض جدول الطلاب
            st.success(f"✅ إجمالي الطلاب: **{len(students_dict)}**")
            # تحويل القاموس إلى DataFrame للعرض
            display_df = pd.DataFrame(
                list(students_dict.items()),
                columns=['رقم الباركود', 'اسم الطالب']
            )
            display_df.index = range(1, len(display_df) + 1)

            # فلتر البحث
            search_student = st.text_input(
                "🔍 بحث عن طالب:",
                placeholder="اكتب الاسم أو الرقم..."
            )
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

            # ✅ عرض الملف الخام إذا وجد
            if not students_df.empty:
                with st.expander("📄 عرض بيانات الملف الكاملة"):
                    st.dataframe(students_df, use_container_width=True)

    # ══════════════════════════════════════════════════════════
    # TAB 3: سجل الحضور الكامل
    # ══════════════════════════════════════════════════════════
    with tab3:
        st.header("📊 سجل الحضور الكامل")
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
            if not df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    search = st.text_input(
                        "🔍 بحث بالاسم:", placeholder="اكتب الاسم..."
                    )
                with col2:
                    date_filter = st.date_input("📅 فلترة بالتاريخ:", value=None)

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

    # ══════════════════════════════════════════════════════════
    # TAB 4: تقرير اليوم
    # ══════════════════════════════════════════════════════════
    with tab4:
        st.header(f"📋 تقرير يوم {datetime.now().strftime('%Y-%m-%d')}")
        today_names = get_attended_today()

        # ── بطاقات الإحصائيات ─────────────────────────
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='info-card'>
                <h2 style='color:white; margin:0;'>{len(today_names)}</h2>
                <p style='color:white; margin:0;'>✅ حاضر اليوم</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            total = len(students_dict) if students_dict else 0
            st.markdown(f"""
            <div class='info-card'>
                <h2 style='color:white; margin:0;'>{total}</h2>
                <p style='color:white; margin:0;'>🎓 إجمالي الطلاب</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            absent = total - len(today_names) if total > 0 else "—"
            st.markdown(f"""
            <div class='info-card'>
                <h2 style='color:white; margin:0;'>{absent}</h2>
                <p style='color:white; margin:0;'>❌ غائب</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")

        # ── قوائم الحاضرين والغائبين ──────────────────
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("✅ الحاضرون:")
            if today_names:
                for i, name in enumerate(sorted(today_names), 1):
                    st.markdown(f"""
                    <div style='background:#e8f5e9; padding:0.5rem 1rem; border-radius:8px; margin:0.3rem 0; border-right:4px solid #4caf50;'>
                        {i}. {name}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📭 لا يوجد حضور اليوم بعد")
        with col2:
            st.subheader("❌ الغائبون:")
            if students_dict:
                attended_names = set(today_names)
                all_names = set(students_dict.values())
                absent_names = all_names - attended_names
                if absent_names:
                    for i, name in enumerate(sorted(absent_names), 1):
                        st.markdown(f"""
                        <div style='background:#ffebee; padding:0.5rem 1rem; border-radius:8px; margin:0.3rem 0; border-right:4px solid #f44336;'>
                            {i}. {name}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("🎉 جميع الطلاب حاضرون!")
            else:
                st.info("لا توجد بيانات طلاب")

# ============================================================
# ▶️ تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    main()
