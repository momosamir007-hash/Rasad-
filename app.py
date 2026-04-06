import cv2 import numpy as np import urllib.request import urllib.error from pyzbar.pyzbar import decode from datetime import datetime import pandas as pd import os import time

# ============================================================
# ⚙️ الإعدادات الأساسية
# ============================================================
# رابط كاميرا الهاتف عبر تطبيق IP Webcam
CAMERA_URL = 'http://192.168.1.5:8080/shot.jpg'
# اسم ملف الحضور
ATTENDANCE_FILE = 'attendance.csv'
# ملف بيانات الطلاب (اختياري)
STUDENTS_FILE = 'students.xlsx'
# وقت الانتظار بين المحاولات (بالثواني)
RETRY_DELAY = 2

# ============================================================
# 📋 قائمة الأسماء المسجلة في الجلسة الحالية
# ============================================================
scanned_in_session = set()  # استخدام set بدلاً من list للأداء الأفضل

# ============================================================
# 🔧 دوال مساعدة
# ============================================================
def initialize_attendance_file():
    """ إنشاء ملف الحضور إذا لم يكن موجوداً مع إضافة العناوين """
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['الاسم/الرقم', 'التاريخ والوقت', 'الحالة'])
        df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ تم إنشاء ملف الحضور: {ATTENDANCE_FILE}")
    else:
        print(f"📂 تم العثور على ملف الحضور: {ATTENDANCE_FILE}")

def load_students_data():
    """ تحميل بيانات الطلاب من ملف الإكسيل
        يُرجع قاموساً: {رقم_الباركود: اسم_الطالب} """
    students_dict = {}
    if os.path.exists(STUDENTS_FILE):
        try:
            df = pd.read_excel(STUDENTS_FILE)
            # التأكد من وجود الأعمدة المطلوبة
            # المتوقع: عمود 'barcode' وعمود 'name'
            if 'barcode' in df.columns and 'name' in df.columns:
                for _, row in df.iterrows():
                    students_dict[str(row['barcode'])] = str(row['name'])
                print(f"✅ تم تحميل {len(students_dict)} طالب من قاعدة البيانات")
            else:
                print("⚠️ تنبيه: ملف الطلاب يجب أن يحتوي على أعمدة 'barcode' و 'name'")
        except Exception as e:
            print(f"❌ خطأ في قراءة ملف الطلاب: {e}")
    else:
        print(f"ℹ️ ملف الطلاب غير موجود - سيتم استخدام بيانات الباركود مباشرة")
    return students_dict

def get_already_attended_today():
    """ جلب قائمة من سجّلوا حضورهم اليوم من الملف """
    attended_today = set()
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE, encoding='utf-8-sig')
            if not df.empty and 'التاريخ والوقت' in df.columns:
                # فلترة سجلات اليوم فقط
                df['date_only'] = pd.to_datetime(
                    df['التاريخ والوقت'], errors='coerce'
                ).dt.strftime('%Y-%m-%d')
                today_records = df[df['date_only'] == today]
                attended_today = set(today_records['الاسم/الرقم'].tolist())
    except Exception as e:
        print(f"⚠️ خطأ في قراءة سجلات اليوم: {e}")
    return attended_today

def mark_attendance(identifier, students_dict):
    """ تسجيل الحضور في الملف
        المعاملات:
            identifier: رقم الباركود أو الـ QR
            students_dict: قاموس بيانات الطلاب
        يُرجع: tuple: (نجح_التسجيل, اسم_الشخص, الرسالة) """
    # جلب الاسم من القاموس أو استخدام الرقم مباشرة
    name = students_dict.get(identifier, identifier)
    # التحقق من عدم التكرار في الجلسة الحالية
    if identifier in scanned_in_session:
        return False, name, "مسجّل مسبقاً في هذه الجلسة"
    # التحقق من عدم التكرار في نفس اليوم
    attended_today = get_already_attended_today()
    if name in attended_today or identifier in attended_today:
        scanned_in_session.add(identifier)  # إضافة للجلسة لتجنب التحقق المتكرر
        return False, name, "مسجّل مسبقاً اليوم"
    # تسجيل الحضور
    try:
        now = datetime.now()
        dt_string = now.strftime('%Y-%m-%d %H:%M:%S')
        # إضافة السجل الجديد
        new_record = pd.DataFrame({
            'الاسم/الرقم': [name],
            'التاريخ والوقت': [dt_string],
            'الحالة': ['حاضر']
        })
        # إضافة للملف بدون كتابة العناوين مجدداً
        new_record.to_csv(
            ATTENDANCE_FILE,
            mode='a',      # وضع الإضافة
            header=False,  # بدون عناوين
            index=False,
            encoding='utf-8-sig'
        )
        # إضافة للجلسة الحالية
        scanned_in_session.add(identifier)
        return True, name, f"تم التسجيل بنجاح - {dt_string}"
    except Exception as e:
        return False, name, f"خطأ في التسجيل: {e}"

def draw_barcode_info(img, barcode, name, success):
    """ رسم معلومات الباركود على الصورة
        المعاملات:
            img: الصورة
            barcode: كائن الباركود المكتشف
            name: اسم/رقم الشخص
            success: هل تم التسجيل بنجاح """
    # اختيار لون المربع حسب حالة التسجيل
    # أخضر = تسجيل ناجح، أصفر = مسجّل مسبقاً
    color = (0, 255, 0) if success else (0, 255, 255)
    # رسم المضلع حول الباركود
    pts = np.array([barcode.polygon], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, color, 3)
    # إضافة خلفية للنص لتحسين القراءة
    rect = barcode.rect
    text_x = rect[0]
    text_y = rect[1] - 10
    # قياس حجم النص
    (text_width, text_height), _ = cv2.getTextSize(
        name, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2
    )
    # رسم خلفية النص
    cv2.rectangle(
        img,
        (text_x - 5, text_y - text_height - 5),
        (text_x + text_width + 5, text_y + 5),
        color,
        -1  # ملء المستطيل
    )
    # كتابة الاسم
    cv2.putText(
        img, name, (text_x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2
    )
    return img

def draw_stats_panel(img, total_today):
    """ إضافة لوحة إحصائيات في أعلى الشاشة """
    panel_height = 60
    overlay = img.copy()
    # خلفية شبه شفافة
    cv2.rectangle(overlay, (0, 0), (img.shape[1], panel_height), (50, 50, 50), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    # معلومات الوقت الحالي
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cv2.putText(
        img, f"Time: {current_time}", (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1
    )
    # عدد الحاضرين
    session_count = len(scanned_in_session)
    cv2.putText(
        img, f"Session: {session_count} | Today: {total_today}", (10, 50),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 150), 1
    )
    return img

def capture_frame(url, timeout=5):
    """ التقاط إطار من كاميرا الهاتف
        يُرجع: الصورة أو None في حالة الخطأ """
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        img_array = np.array(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)
        return img
    except urllib.error.URLError:
        return None
    except Exception:
        return None

# ============================================================
# 🚀 الدالة الرئيسية
# ============================================================
def main():
    print("=" * 50)
    print(" 📷 نظام تسجيل الحضور بالباركود")
    print("=" * 50)

    # تهيئة الملفات
    initialize_attendance_file()
    students_dict = load_students_data()

    print(f"\n📡 محاولة الاتصال بالكاميرا: {CAMERA_URL}")
    print("⌨️ اضغط 'q' للخروج | 's' لحفظ لقطة شاشة\n")

    # متغيرات الحالة
    connection_errors = 0
    max_errors = 10
    last_message = ""
    message_timer = 0

    while True:
        # التقاط الإطار
        img = capture_frame(CAMERA_URL)

        # التعامل مع خطأ الاتصال
        if img is None:
            connection_errors += 1
            print(f"⚠️ خطأ في الاتصال ({connection_errors}/{max_errors})")
            if connection_errors >= max_errors:
                print("❌ تعذر الاتصال بالكاميرا. تحقق من:")
                print(" 1. أن الهاتف والحاسوب على نفس الشبكة")
                print(" 2. أن تطبيق IP Webcam يعمل")
                print(f" 3. صحة الرابط: {CAMERA_URL}")
                break
            time.sleep(RETRY_DELAY)
            continue

        # إعادة تعيين عداد الأخطاء عند النجاح
        connection_errors = 0

        # جلب إحصائيات اليوم
        total_today = len(get_already_attended_today())

        # ============================================================
        # 🔍 قراءة الباركود
        # ============================================================
        detected_barcodes = decode(img)

        for barcode in detected_barcodes:
            # قراءة البيانات
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            print(f"🔍 تم اكتشاف {barcode_type}: {barcode_data}")

            # تسجيل الحضور
            success, name, message = mark_attendance(barcode_data, students_dict)

            # عرض رسالة في الطرفية
            if success:
                print(f" ✅ {message}")
            else:
                print(f" ℹ️ {name}: {message}")

            # تخزين آخر رسالة للعرض على الشاشة
            last_message = f"{'✓' if success else '!'} {name}"
            message_timer = 50  # عرض الرسالة لـ 50 إطار

            # رسم معلومات الباركود
            img = draw_barcode_info(img, barcode, name, success)

        # إضافة لوحة الإحصائيات
        img = draw_stats_panel(img, total_today)

        # عرض آخر رسالة
        if message_timer > 0:
            color = (0, 255, 0) if '✓' in last_message else (0, 255, 255)
            cv2.putText(
                img, last_message,
                (img.shape[1] - 300, img.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
            )
            message_timer -= 1

        # عرض الصورة
        cv2.imshow('🎓 Attendance System', img)

        # معالجة المفاتيح
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n👋 تم إنهاء البرنامج")
            break
        elif key == ord('s'):
            # حفظ لقطة شاشة
            screenshot_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(screenshot_name, img)
            print(f"📸 تم حفظ لقطة الشاشة: {screenshot_name}")

    cv2.destroyAllWindows()

    # ============================================================
    # 📊 ملخص الجلسة
    # ============================================================
    print("\n" + "=" * 50)
    print("📊 ملخص الجلسة:")
    print(f" • عدد المسجلين في هذه الجلسة: {len(scanned_in_session)}")
    print(f" • الأشخاص: {', '.join(scanned_in_session) if scanned_in_session else 'لا أحد'}")
    print("=" * 50)

# ============================================================
# ▶️ نقطة البداية
# ============================================================
if __name__ == "__main__":
    main()
