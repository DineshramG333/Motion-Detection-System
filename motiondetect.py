import cv2
import numpy as np
import time
import os
import sys
from datetime import datetime

CAMERA_INDEX = 0
MIN_CONTOUR_AREA = 1800
BLUR_KERNEL = (15, 15)
VAR_THRESHOLD = 30
LOG_FILE = "bank_security_log.txt"
BEEP_COOLDOWN = 1.0

def play_alert_sound():
    if sys.platform.startswith('win'):
        import winsound
        winsound.Beep(2000, 150)
    elif sys.platform.startswith('darwin'):
        os.system('say -v Ping "alarm" &')
    else:
        print('\a', end='', flush=True)

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError("Camera error")

    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=600, varThreshold=VAR_THRESHOLD, detectShadows=True)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    
    last_log_time = 0.0
    last_beep_time = 0.0
    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, BLUR_KERNEL, 0)

            fg_mask = bg_subtractor.apply(blurred)
            _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_found = False

            for c in contours:
                if cv2.contourArea(c) < MIN_CONTOUR_AREA:
                    continue
                motion_found = True
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "TARGET DETECTED", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 35), (20, 20, 20), -1)
            cv2.putText(frame, f"CAM-01 | VAULT ZONE | {timestamp}", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if motion_found:
                cv2.circle(frame, (25, 55), 8, (0, 0, 260), -1)
                cv2.putText(frame, "BREACH DETECTED", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                if now - last_beep_time >= BEEP_COOLDOWN:
                    play_alert_sound()
                    last_beep_time = now

                if now - last_log_time >= 1.0:
                    with open(LOG_FILE, "a") as f:
                        f.write(f"[{timestamp}] SECURITY ALARM: Motion detected in surveillance zone\n")
                    last_log_time = now
            else:
                cv2.circle(frame, (25, 55), 8, (0, 255, 0), -1)
                cv2.putText(frame, "SECURE", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("BANK SURVEILLANCE SYSTEM", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
