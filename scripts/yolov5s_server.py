from flask import Flask
import logging
import torch
import threading
from ultralytics import YOLO
from models import stream, notifications

app = Flask(__name__)
logger = logging.getLogger(__name__)

model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
TARGET_OBJECT = "person"

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
            _stream.stop()

def yolo_process(frame):
    results = model(frame)
    detected_objects = results.pandas().xywh[0]    
    for _, row in detected_objects.iterrows():
        if row['name'].lower() == TARGET_OBJECT.lower():
            print(f"{TARGET_OBJECT} detected!")
            notifs.send_notification(self.cam_index)
            time.sleep(5) #TODO: enhance the time interval between detections

streams = []
for i in range(streams_range):
    _stream = Stream(cam_index=i)
    if _stream.is_opened:
        streams.append(_stream)


def start():
    threading.Thread(target=main, daemon=True).start()
    app.run(host='0.0.0.0', port=5002, threaded=True)
