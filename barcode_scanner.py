import numpy as np, cv2
try:
 from pyzbar.pyzbar import decode; PYZBAR=True
except Exception: PYZBAR=False
def scan_barcodes(image):
 arr=np.array(image.convert('RGB')); bgr=cv2.cvtColor(arr,cv2.COLOR_RGB2BGR); out=[]
 if PYZBAR:
  try:
   for x in decode(bgr):
    v=x.data.decode('utf-8',errors='ignore').strip()
    if v:out.append((v,x.type))
  except Exception:pass
 if not out:
  try:
   v,_,_=cv2.QRCodeDetector().detectAndDecode(bgr)
   if v:out.append((v.strip(),'QRCODE'))
  except Exception:pass
 return list(dict.fromkeys(out))
