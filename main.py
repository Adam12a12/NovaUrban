from flask import Flask, Response
import cv2
import threading
from typing import Optional, Tuple


app = Flask(__name__)

usb_cam_range = 5


class Camera:

    def __init__(self, user = None, password = None, ip = None, port = None, stream_path = None, cam_index = None):
        if cam_index is not None:
            self.cap = cv2.VideoCapture(cam_index)
        else:    
            self.url = f"rtsp://{user}:{password}@{ip}:{port}/{stream_path}"
            self.cap = cv2.VideoCapture(self.url)
        if self.cap.isOpened():
            self.is_opened = True
            self.is_running = False
            self.lock = threading.Lock()
            self.frame: Optional[Tuple[bool, cv2.Mat]] = None
        else:
            self.is_opened = False

    def start(self) -> None:
        self.is_running = True
        thread = threading.Thread(target=self._update_frame, args=())
        thread.start()

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

@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    return Response(gen_frames(camera_index),mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames(camera_index):
    while True:
        success, frame = cameras[camera_index].read()
        if success:
            ret, buffer = cv2.imencode('.jpg', frame)
            stream = buffer.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream + b'\r\n')

def main():
    for i in range(len(cameras)):
        cameras[i].start()

        try:
            while True:
                ret, frame = cameras[i].read()
                if not ret:
                    print("Failed to get frame")
        finally:
            camera.stop()

cameras = []
for i in range(usb_cam_range):
    camera = Camera(cam_index=i)
    if camera.is_opened:
        cameras.append(camera)

#TODO: Add second loop to handle ip cameras

if __name__ == "__main__":
    threading.Thread(target=main, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, threaded=True)