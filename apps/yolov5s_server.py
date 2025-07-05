from flask import Flask
import logging
import torch
import threading
from ultralytics import YOLO
from models import notifications
from typing import Optional, Tuple
import cv2

class Stream:

    def __init__(self, cam_index):
        self.cam_index = cam_index
        url = f"http://localhost:5000/video_feed/{cam_index}"
        self.cap = cv2.VideoCapture(url)
        if self.cap.isOpened():
            self.is_opened = True
            self.is_running = False
            self.lock = threading.Lock()
            self.frame: Optional[Tuple[bool, cv2.Mat]] = None
        else:
            self.is_opened = False

    def start(self, yolo=False) -> None:
        self.is_running = True
        update_thread = threading.Thread(target=self._update_frame, args=())
        if yolo:
            process_thread = threading.Thread(target=self.yolov11_processing, args=())
        else:
            process_thread = threading.Thread(target=self.nova_urban_processing, args=())
        update_thread.start()
        process_thread.start()

    def stop(self) -> None:
        self.is_running = False
        if self.cap.isOpened():
            self.cap.release()

    def _update_frame(self) -> None:
        while self.is_running:
            ret, frame = self.cap.read()
            with self.lock:
                self.frame = (ret, frame)

    def read(self) -> Tuple[bool, Optional[cv2.Mat]]:
        with self.lock:
            if self.frame is not None:
                return self.frame
            return False, None

    def nova_urban_processing(self):
        while self.is_running:
            nu_process(self.frame)

    def yolov11_processing(self):
        while self.is_running:
            process(self.frame)

streams_range = 5
streams = []

app = Flask(__name__)
logger = logging.getLogger(__name__)

model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
TARGET_OBJECT = os.getenv('TARGET_OBJECT')

notifs = notifications.Notifications()

def main():
    for i in range(len(streams)):
        streams[i].start(yolo=True)

        try:
            while True:
                ret, frame = streams[i].read()
                # if not ret:
                #     print("Failed to get frame")
        finally:
            stream.stop()

def process(frame):
    results = model(frame)
    detected_objects = results.pandas().xywh[0]    
    for _, row in detected_objects.iterrows():
        if row['name'].lower() == TARGET_OBJECT.lower():
            print(f"{TARGET_OBJECT} detected!")
            notifs.send_notification(self.cam_index)
            time.sleep(5) #TODO: enhance the time interval between detections


def start():
    for i in range(streams_range):
        stream = Stream(cam_index=i)
        if stream.is_opened:
            streams.append(stream)
    threading.Thread(target=main, daemon=True).start()
    app.run(host='0.0.0.0', port=5002, threaded=True)
