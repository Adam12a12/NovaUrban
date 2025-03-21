from flask import Flask, request, jsonify, Response, render_template, url_for
import logging
from pyfcm import FCMNotification
import cv2
import os
from dotenv import load_dotenv
from datetime import datetime
import torch
import threading
import time

#TODO: This file will implement AI processing and notifications

load_dotenv()
DEVICE_TOKEN = os.getenv('DEVICE_TOKEN')
SERVER_KEY = os.getenv('SERVER_KEY')
PROJECT_ID = os.getenv('PROJECT_ID')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
logger = logging.getLogger(__name__)
fcm = FCMNotification(service_account_file="env/novaurban-7d541-firebase-adminsdk-flrke-80914775d4.json", project_id=PROJECT_ID)

# Used for debugging purposes and imshow()
os.environ["XDG_SESSION_TYPE"] = "xcb"
QT_DEBUG_PLUGINS=1
is_recording = False

# yolo testing stuff
# model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
# TARGET_OBJECT = "person"

cameras = []
camera_count = 5
for i in range(camera_count):
    cap = cv2.VideoCapture(i)
    if cap.isOpened:
        cameras.append(cap)
processed_frames = {i: None for i in range(camera_count)}
locks = [threading.Lock() for _ in range(camera_count)]

def send_notification(camera_index):
    now = datetime.now()
    today = datetime.today()
    time = now.strftime('%H:%M:%S')
    date = today.strftime('%d-%m-%Y')
    data = { 
        # 'time': time,
        # 'date': date,
        # 'camera_index':  camera_index
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


@app.route('/')
def index():
    return render_template('base.html')


# def check_for_target_object(frame, model, camera_index):
#     results = model(frame)
#     detected_objects = results.pandas().xywh[0]    
#     for _, row in detected_objects.iterrows():
#         if row['name'].lower() == TARGET_OBJECT.lower():
#             print(f"{TARGET_OBJECT} detected!")
#             # send_notification(camera_index)
#             time.sleep(5) #TODO: enhance the time interval between detections

def process(camera_index):
    while True:
        with locks[camera_index]:
            success, frame = cameras[camera_index].read()
            if success:
                ret, buffer = cv2.imencode('.jpg', frame)
                # check_for_target_object(frame, model, camera_index)
                processed_frames[camera_index] = buffer.tobytes()
        
def gen_frames(camera_index):
    while True:
        frame = processed_frames[camera_index]
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    return Response(gen_frames(camera_index),mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    for i in range(camera_count):
        threading.Thread(target=process, args=(i,), daemon=True).start()
    app.run(host='0.0.0.0', port=5000, threaded=True)
