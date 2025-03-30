from typing import Optional, Tuple
import cv2
import threading
from scripts.yolov5s_server import yolo_process
from scripts.nova_urban_server import nu_process

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

    def start(self, yolo=False) -> None:
        self.is_running = True
        update_thread = threading.Thread(target=self._update_frame, args=())
        if yolo:
            process_thread = threading.Thread(target=self.yolov11_processing, args=())
        else:
            process_thread = threading.Thread(target=self.nova_urban_processing, args=())
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

    def nova_urban_processing(self):
        while self.is_running:
            nu_process(self.frame)

    def yolov11_processing(self):
        while self.is_running:
            yolo_process(self.frame)