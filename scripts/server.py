from flask import Flask, Response
import cv2
import threading
from models import camera

app = Flask(__name__)

usb_cam_range = 5

@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    return Response(gen_frames(camera_index),mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames(camera_index):
    while True:
        success, frame = cams[camera_index].read()
        if success:
            ret, buffer = cv2.imencode('.jpg', frame)
            stream = buffer.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream + b'\r\n')

def main():
    for i in range(len(cams)):
        cams[i].start()

        try:
            while True:
                ret, frame = cams[i].read()
                # if not ret:
                #     print("Failed to get frame")
        finally:
            cam.stop()

cams = []
for i in range(usb_cam_range):
    cam = camera.Camera(cam_index=i)
    if cam.is_opened:
        cams.append(cam)

#TODO: Add second loop to handle ip cameras

def start():
    threading.Thread(target=main, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, threaded=True)