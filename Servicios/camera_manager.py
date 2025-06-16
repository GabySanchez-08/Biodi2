import cv2
import platform
from typing import Tuple, Optional

class CameraManager:
    def __init__(self, index: int = 0, width=1920, height=1080):
        self.index = index
        self.cap = None
        self.width = width
        self.height = height

    def open(self):
        backend = cv2.CAP_AVFOUNDATION if platform.system()=="Darwin" \
                  else cv2.CAP_DSHOW if platform.system()=="Windows" \
                  else None
        self.cap = cv2.VideoCapture(self.index, backend) if backend else cv2.VideoCapture(self.index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self) -> Optional[cv2.Mat]:
        if not (self.cap and self.cap.isOpened()):
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def set_zoom(self, value: float) -> bool:
        return self.cap.set(cv2.CAP_PROP_ZOOM, value)

    def set_focus(self, value: float) -> bool:
        return self.cap.set(cv2.CAP_PROP_FOCUS, value)

    def close(self):
        if self.cap:
            self.cap.release()