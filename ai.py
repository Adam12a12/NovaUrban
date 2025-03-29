from flask import Flask, request, jsonify, Response
import logging
from pyfcm import FCMNotification
import cv2
import os
from dotenv import load_dotenv
from datetime import datetime
import torch
import threading
import time
from ultralytics import YOLO
from typing import Optional, Tuple


load_dotenv()
DEVICE_TOKEN = os.getenv('DEVICE_TOKEN')
SERVER_KEY = os.getenv('SERVER_KEY')
PROJECT_ID = os.getenv('PROJECT_ID')

streams_range = 5

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
logger = logging.getLogger(__name__)
fcm = FCMNotification(service_account_file="env/novaurban-7d541-firebase-adminsdk-flrke-80914775d4.json", project_id=PROJECT_ID)

WEIGHTS = {
    'yolo': 0.7,
    'resnet': 0.3
}

yolo_model = YOLO('ai_models/best.pt', task="predict")
resnet_model = load_model('ai_models/resnet50_model.h5')

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

    def start(self) -> None:
        self.is_running = True
        update_thread = threading.Thread(target=self._update_frame, args=())
        process_thread = threading.Thread(target=self.process_frames, args=())
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

    def prepare_frame(frame):
        frame = cv2.resize(frame, (224, 224))
        frame = img_to_array(frame)
        frame = np.expand_dims(frame, axis=0)
        frame = preprocess_input(frame)
        return frame

    def process_frames(self):
        while self.is_running:
            results = yolo_model(self.frame)
            detections = results[0].boxes
            yolo_hazard = 1 if len(detections) > 0 else 0

            preprocessed_frame = prepare_frame(self.frame)
            resnet_prediction = resnet_model.predict(preprocessed_frame)
            resnet_hazard = 1 if np.argmax(resnet_prediction) == 1 else 0
            
            vote = weighted_voting(yolo_hazard, resnet_hazard)

            detections_data = results[0].boxes.data.cpu().numpy()
            yolo_results = [{'class_id': int(det[5]), 'confidence': float(det[4]), 'x_min': float(det[0]), 'y_min': float(det[1]), 'x_max': float(det[2]), 'y_max': float(det[3])} for det in detections_data]

            if vote == 1:
                send_notification(self.cam_index)

def weighted_voting(yolo_result, resnet_result):
    weighted_sum = (yolo_result * WEIGHTS['yolo'] + resnet_result * WEIGHTS['resnet'])
    return 1 if weighted_sum > 0.5 else 0

def send_notification(camera_index):
    now = datetime.now()
    today = datetime.today()
    time = now.strftime('%H:%M:%S')
    date = today.strftime('%d-%m-%Y')
    data = { 
        'time': time,
        'date': date,
        'camera_index':  camera_index
        } 
    title = 'Danger Alert'
    body = 'Danger description'
    # TODO: data fcm.notify returns payload type error
    result = fcm.notify(fcm_token=DEVICE_TOKEN,notification_title=title,notification_body=body, data_payload=data)
    print (result)


@app.route('/register_token', methods=['POST'])
def register_token():
    data = request.get_json()
    token = data.get('token')
    if token:
        DEVICE_TOKEN = token
        return jsonify({'status': 'success', 'message': 'Token received'}), 200 
    else: 
        return jsonify({'status': 'error', 'message': 'No token provided'}), 400


def main():
    for i in range(len(streams)):
        streams[i].start()

        try:
            while True:
                ret, frame = streams[i].read()
                if not ret:
                    print("Failed to get frame")
        finally:
            stream.stop()

streams = []
for i in range(streams_range):
    stream = Stream(cam_index=i)
    if stream.is_opened:
        streams.append(stream)


if __name__ == '__main__':
    threading.Thread(target=main, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, threaded=True)
