import time
import requests
from datetime import datetime
import cv2
import imutils
import numpy as np
import sys

# ---------- Postavke nodea ----------
node_id = 1  # može i sys.argv[1] za fleksibilnost
camera_idx = int(node_id)

# ---------- Parametri detekcije ----------
# ---------- Novi osjetljiviji parametri ----------
POS_TH = 7       # osjetljivije na pozitivne promjene
NEG_TH = -7      # osjetljivije na negativne promjene
ALARM_EVENT_COUNT = 2000   # puno manje događaja treba za alarm
ALARM_PERSIST = 5          # kraći broj frameova za uzastopnu detekciju
COOLDOWN_SEC = 2

# ---------- Inicijalizacija kamere ----------
cap = cv2.VideoCapture(camera_idx)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

ret, frame = cap.read()
if not ret:
    raise RuntimeError(f"[ERROR] Cannot access webcam {camera_idx}.")

frame = imutils.resize(frame, width=640)
prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
prev_gray = cv2.GaussianBlur(prev_gray, (7, 7), 0)

alarm_counter = 0
last_sent_time = 0

# ---------- Glavna petlja ----------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = imutils.resize(frame, width=640)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # ---------- Simulacija EBV ----------
    diff = cv2.subtract(gray, prev_gray).astype(np.int16)
    pos_events = (diff > POS_TH).astype(np.uint8) * 255
    neg_events = (diff < NEG_TH).astype(np.uint8) * 255

    event_img = np.zeros((*pos_events.shape, 3), dtype=np.uint8)
    event_img[..., 1] = pos_events   # Zeleno (ON)
    event_img[..., 2] = neg_events   # Crveno (OFF)
    cv2.imshow(f"Node {node_id} - Simulated EBV", event_img)

    # ---------- Logika detekcije pokreta ----------
    event_count = (pos_events.sum() + neg_events.sum()) // 255
    if event_count > ALARM_EVENT_COUNT:
        alarm_counter += 1
    else:
        alarm_counter = max(alarm_counter - 1, 0)

    if alarm_counter > ALARM_PERSIST and (time.time() - last_sent_time) > COOLDOWN_SEC:
        timestamp = datetime.now().isoformat()
        print(f"[INFO] 🚨 Motion detected on Node {node_id} at {timestamp}")
        try:
            requests.post("http://localhost:5000/motion", json={
                "node_id": node_id,
                "timestamp": timestamp
            })
            last_sent_time = time.time()
        except Exception as e:
            print(f"[ERROR]  Failed to send detection: {e}")
        # *NE* resetiramo alarm_counter, neka nastavi ako aktivnost traje

    prev_gray = gray

    # ---------- Tipka za izlaz ----------
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
