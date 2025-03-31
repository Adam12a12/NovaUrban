from typing import Optional, Tuple
import cv2
import threading

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