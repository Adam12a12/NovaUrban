import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import time
import torch
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.resnet50 import preprocess_input
import requests
import smtplib
from twilio.rest import Client
from email.mime.text import MIMEText
import os
from ultralytics import YOLO
from dotenv import load_dotenv
from PIL import Image
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app)

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
email_address = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_PASSWORD")

CAMERA_URL = "http://172.16.26.49:8080/video"

WEIGHTS = {
    'yolo': 0.7,
    'resnet': 0.3
}

BASE_DIR = Path(__file__).resolve().parent


IMAGES_FOLDER = BASE_DIR / "pictures"

OUTPUT_FOLDER = BASE_DIR / "output"

yolo_model = YOLO(BASE_DIR / "ai_models/best.pt", task="predict")

RESNET_MODEL_PATH = BASE_DIR / "ai_models/resnet50_model.h5"
resnet_model = load_model(RESNET_MODEL_PATH)

VIDEO_STREAM = cv2.VideoCapture(CAMERA_URL)

if not VIDEO_STREAM.isOpened():
    logger.error("Unable to connect to CV")
else:
    logger.info("CV connected")

def preprocess_image(image):
    image = cv2.resize(image, (224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)
    return image

def weighted_voting(yolo_result, resnet_result):
    weighted_sum = (yolo_result * WEIGHTS['yolo'] + resnet_result * WEIGHTS['resnet'])
    return 1 if weighted_sum > 0.5 else 0

def send_whatsapp_alert(message):
    client = Client(account_sid, auth_token)
    from_whatsapp_number = 'whatsapp:+14155238886'
    to_whatsapp_number = 'whatsapp:+966561227480'
    try:
        msg = client.messages.create(body=message, from_=from_whatsapp_number, to=to_whatsapp_number)
        logger.info(f"WhatsApp message sent: {msg.sid}")
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")

def send_telegram_alert(message):
    url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
    params = {'chat_id': telegram_chat_id, 'text': message}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            logger.info("Telegram message sent")
        else:
            logger.warning(f"Telegram message sending failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def send_email_alert(subject, message, to_email):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_address, email_password)
            server.sendmail(email_address, to_email, msg.as_string())
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def send_alert(message):
    send_whatsapp_alert(message)
    send_telegram_alert(message)
    send_email_alert("Danger alert", message, email_address)

@app.route('/')
def index():
    return render_template('base.html')

def get_video_frame():
    global VIDEO_STREAM
    if not VIDEO_STREAM.isOpened():
        logger.error("Unable to open video with OpenCV")
        return None

    ret, frame = VIDEO_STREAM.read()
    if not ret:
        logger.error("Error reading video frame")
        return None

    logger.info("Video frame read successfully")
    return frame

@socketio.on('connect')
def handle_connect(sid):
    start_time = time.time()
    while True:
        frame = get_video_frame()
        if frame is not None:
            results = yolo_model(frame)
            detections = results[0].boxes
            yolo_hazard = 1 if len(detections) > 0 else 0
            logger.info(f"YOLO results: {yolo_hazard}")

            preprocessed_frame = preprocess_image(frame)
            resnet_prediction = resnet_model.predict(preprocessed_frame)
            resnet_hazard = 1 if np.argmax(resnet_prediction) == 1 else 0
            logger.info(f"ResNet50 results: {resnet_hazard}")

            vote = weighted_voting(yolo_hazard, resnet_hazard)
            logger.info(f"Weighted vote results: {vote}")


            detections_data = results[0].boxes.data.cpu().numpy()
            yolo_results = [{'class_id': int(det[5]), 'confidence': float(det[4]), 'x_min': float(det[0]), 'y_min': float(det[1]), 'x_max': float(det[2]), 'y_max': float(det[3])} for det in detections_data]


            socketio.emit('hazard_update', {
                'yolo_results': yolo_results,
                'resnet_results': int(resnet_hazard),
                'weighted_vote': int(vote)
            })


            if vote == 1:
                send_alert("Danger detected on site!")

            if time.time() - start_time >= 10:
                logger.info("Detecting worked correctly!")
                start_time = time.time()

            time.sleep(1)
        else:
            logger.error("Failed getting camera frame")
            break

def process_images():
    processed_count = 0
    dangerous_images = []
    for image_file in image_files:
        try:
            frame = cv2.imread(image_file)
            if frame is None:
                logger.warning(f"Error reading image: {image_file} Skipping.")
                continue

            results = yolo_model(frame)
            detections = results[0].boxes.data.cpu().numpy() if len(results[0].boxes) > 0 else []

            draw_detections(frame, detections)
            output_path = os.path.join(OUTPUT_FOLDER, f"result_{os.path.basename(image_file)}")
            cv2.imwrite(output_path, frame)
            logger.info(f"Edited image is saved in: {output_path}")
            processed_count += 1
            if not any([det[5] == 0 for det in detections]):
                dangerous_images.append(f"results/{os.path.basename(output_path)}")
                message = "No helmet detected in the image."
                send_email(output_path, "Warnging: no helmet detected", message)
                send_telegram_message(output_path, message)

        except Exception as e:
            logger.error(f"Error processing image {image_file}: {e}")

    logger.info(f"Processed {processed_count} images out of {len(image_files)} image.")
    return dangerous_images


@app.route('/start_processing')
def start_processing():
    dangerous_images = process_images()
    return jsonify({'processed_count': len(dangerous_images), 'processed_images': dangerous_images})

if __name__ == "__main__":
    logger.info("Running App")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
