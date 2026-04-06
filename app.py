import cv2
import numpy as np
import urllib.request
from pyzbar.pyzbar import decode
from datetime import datetime
import pandas as pd

# استبدل هذا الرابط بالرابط الذي يظهر في تطبيق IP Webcam في هاتفك
url = 'http://192.168.1.5:8080/shot.jpg'

# قائمة لتخزين الأشخاص الذين تم تسجيل حضورهم في الجلسة الحالية لتجنب التكرار
scanned_names = []

def mark_attendance(name):
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
            print(f"تم تسجيل حضور: {name}")

# قراءة بيانات الطلاب من ملف الإكسيل (اختياري لربط الباركود بالاسم)
# df = pd.read_excel('students.xlsx')

while True:
    try:
        # جلب الصورة من كاميرا الهاتف
        imgResp = urllib.request.urlopen(url)
        imgNp = np.array(bytearray(imgResp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgNp, -1)
        
        # قراءة الباركود/QR كود من الصورة
        for barcode in decode(img):
            myData = barcode.data.decode('utf-8')
            
            # يمكنك هنا البحث عن myData (رقم الباركود) في ملف الإكسيل لجلب اسم الطالب
            # سنفترض هنا أن الباركود يحتوي على اسم الطالب أو رقمه المباشر
            
            mark_attendance(myData)
            
            # رسم مربع حول الباركود في الشاشة
            pts = np.array([barcode.polygon], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (0, 255, 0), 5)
            
            # عرض البيانات على الشاشة
            pts2 = barcode.rect
            cv2.putText(img, myData, (pts2[0], pts2[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)
            
        # عرض النافذة
        cv2.imshow('Barcode Scanner Attendance', img)
        
        # اضغط على 'q' للخروج
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    except Exception as e:
        print(f"حدث خطأ في الاتصال بالكاميرا: {e}")
        break

cv2.destroyAllWindows()
