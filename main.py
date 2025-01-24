from flask import Flask, request, jsonify, Response, render_template
import logging
from pyfcm import FCMNotification
import cv2
import os
from dotenv import load_dotenv


load_dotenv()
DEVICE_TOKEN = os.getenv('DEVICE_TOKEN')
SERVER_KEY = os.getenv('SERVER_KEY')
PROJECT_ID = os.getenv('PROJECT_ID')

app = Flask(__name__)
logger = logging.getLogger(__name__)
fcm = FCMNotification(service_account_file="env/novaurban-7d541-firebase-adminsdk-flrke-80914775d4.json", project_id=PROJECT_ID)

# Used for debugging purposes and imshow()
os.environ["XDG_SESSION_TYPE"] = "xcb"
QT_DEBUG_PLUGINS=1
is_recording = False


@app.route('/send_notification')
def send():
    data = { 
        'to': DEVICE_TOKEN, 'notification': { 
            'title': 'Danger Alert', 
            'body': 'Danger description' } }
    headers = { 
        'Authorization': 'key=' + SERVER_KEY, 
        'Content-Type': 'application/json',
            }
    title = 'Danger Alert'
    body = 'Danger description'
    result = fcm.notify(fcm_token=DEVICE_TOKEN,notification_title=title,notification_body=body)
    print (result)

@app.route('/video_feed',methods=['GET'])
def video_feed():
    return Response(start_processing(),mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_processing')
def start_processing():
    cam = cv2.VideoCapture(0)

    frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if is_recording:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (frame_width, frame_height))
    
    while True:
        ret, frame = cam.read()
        what, buffer = cv2.imencode('.jpg', frame)
        # cv2.imshow('Camera', frame)
        frame = buffer.tobytes()
        buffer.tobytes() 
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        if is_recording:
            out.write(frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

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

if __name__ == "__main__":
    logger.info("Running App")
    app.run(debug=True, port=5000, host='0.0.0.0')
