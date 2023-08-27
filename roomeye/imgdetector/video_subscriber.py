"""画像取得部

画像を取得するモジュール

"""
import threading
import time
from logging import Logger

import cv2

import roomeye.common.logging_manager as logging_manager

logger: Logger = logging_manager.get_logger()


class VideoSubscriber(threading.Thread):
    """画像を取得するクラス"""

    def __init__(self, url: str | int = 0) -> None:
        super().__init__(name=f"VideoSubscriber_{url}", daemon=True)
        self._alive = True
        self._started = threading.Event()
        self._started.clear()

        self._url: str | int = url
        self._cnt = 0
        self._fps = 0
        self._frame = None

    def kill(self) -> None:
        """スレッドの削除"""
        self._alive = False
        self.join()

    def run(self) -> None:
        """
        スレッドのループ処理
        """
        self._started.wait()
        logger.info({"action": "VideoSubscriber.run", "command": "start"})
        last_time: float = time.perf_counter()
        cap = cv2.VideoCapture(self._url)
        while cap.isOpened() and self._alive:
            try:
                # 動画の1フレーム (1枚分の画像) を取得する
                success, frame = cap.read()
                if success:
                    # fpsの計算
                    self._cnt += 1
                    now_time = time.perf_counter()
                    if now_time - last_time >= 1.0:
                        self._fps = self._cnt
                        self._cnt = 0
                        last_time = now_time
                        logger.info({"action": "receive_video", "fps": self._fps, "success": success})

                    self._frame = frame
                else:
                    event = threading.Event()
                    event.wait(timeout=0.1)
                self._started.wait()
            except Exception as ex:
                logger.exception({"action": "DroneVideo.run", "ex": ex})
        # Release the video capture object and close the display window
        cap.release()
        cv2.destroyAllWindows()
