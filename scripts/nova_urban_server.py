from flask import Flask
import logging
import threading
from ultralytics import YOLO
from tensorflow.keras.models import load_model
import cv2
from models import stream, notifications

streams_range = 5

app = Flask(__name__)
logger = logging.getLogger(__name__)

WEIGHTS = {
    'yolo': 0.7,
    'resnet': 0.3
}

yolo_model = YOLO('ai_models/best.pt', task="predict")
resnet_model = load_model('ai_models/resnet50_model.h5')

notifs = notifications.Notifications()

def weighted_voting(yolo_result, resnet_result):
    weighted_sum = (yolo_result * WEIGHTS['yolo'] + resnet_result * WEIGHTS['resnet'])
    return 1 if weighted_sum > 0.5 else 0


def main():
    for i in range(len(streams)):
        streams[i].start()

        try:
            while True:
                ret, frame = streams[i].read()
                # if not ret:
                #     print("Failed to get frame")
        finally:
            _stream.stop()

def prepare_frame(frame):
        frame = cv2.resize(frame, (224, 224))
        frame = img_to_array(frame)
        frame = np.expand_dims(frame, axis=0)
        frame = preprocess_input(frame)
        return frame

def nu_process(frame):
    results = yolo_model(frame)
    detections = results[0].boxes
    yolo_hazard = 1 if len(detections) > 0 else 0

    preprocessed_frame = prepare_frame(frame)
    resnet_prediction = resnet_model.predict(preprocessed_frame)
    resnet_hazard = 1 if np.argmax(resnet_prediction) == 1 else 0
    
    vote = weighted_voting(yolo_hazard, resnet_hazard)

    detections_data = results[0].boxes.data.cpu().numpy()
    yolo_results = [{'class_id': int(det[5]), 'confidence': float(det[4]), 'x_min': float(det[0]), 'y_min': float(det[1]), 'x_max': float(det[2]), 'y_max': float(det[3])} for det in detections_data]

    if vote == 1:
        notifs.send_notification(self.cam_index)

streams = []
for i in range(streams_range):
    _stream = stream.Stream(cam_index=i)
    if _stream.is_opened:
        streams.append(_stream)


def start():
    threading.Thread(target=main, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, threaded=True)
