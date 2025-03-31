from flask import Flask, Response, render_template
import cv2
import threading
from models import camera

app = Flask(__name__)

usb_cam_range = 5
cams = []

@app.route('/video_feed/all')
def render_all_cams():
    camera_indexes = []
    i = 0
    for cam in cams:
        camera_indexes.append(i)
        i+=1
    return render_template('cameras.html',camera_indexes=camera_indexes)

@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    return Response(gen_frames(camera_index),mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames(camera_index):
    if len(cams) > camera_index:
        while True:
            success, frame = cams[camera_index].read()
            if success:
                ret, buffer = cv2.imencode('.jpg', frame)
                stream = buffer.tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream + b'\r\n')

def main(hw_cam_index):
    for i in range(len(cams)):
        if cams[i].hw_cam_index == hw_cam_index:
            cams[i].start()
            try:
                while True:
                    ret, frame = cams[i].read()
                    # if not ret:
                    #     print("Failed to get frame")
                    #TODO: add a static frame showing that camera frame was not read successfuly
            finally:
                cam.stop()

def start():
    #TODO: Add second loop to handle ip cameras
    for i in range(usb_cam_range):
        cam = camera.Camera(cam_index=i)
        if cam.is_opened:
            cams.append(cam)
            threading.Thread(target=main, daemon=True, args=(i,)).start()
    app.run(host='0.0.0.0', port=5000, threaded=True)