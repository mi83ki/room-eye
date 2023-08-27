import datetime
import logging
import logging.handlers
import os
import os.path
import threading
import time
import traceback

import cv2
import numpy as np
from config import (
    CAMERA_FLIP,
    CAMERA_ROTATE,
    ENABLE_LIEDOWN,
    ENABLE_SECOND_CAMERA,
    LIE_DOWN_CNT_THREASHOLD,
    NO_PERSON_TIME_THREASHOLD,
    PERSON_CNT_THREASHOLD,
)
from CvFpsCalc import CvFpsCalc
from dotenv import load_dotenv
from HumanDetector import HumanDetector
from LieDownDetector import LieDownDetector
from NatureRemoController.NatureRemoController import NatureRemoController

# logsフォルダが無ければ作成する
if os.path.isdir("logs") is False:
    os.mkdir("logs")
if os.path.isdir("logs/img") is False:
    os.mkdir("logs/img")
# ロガーを取得する
logger = logging.getLogger("RoomEye")
logger.setLevel(logging.DEBUG)  # 出力レベルを設定
# ハンドラー1を生成する
h1 = logging.StreamHandler()
h1.setLevel(logging.DEBUG)  # 出力レベルを設定
# ハンドラー2を生成する
# h2 = logging.FileHandler('logs/RoomEye.log')
h2 = logging.handlers.TimedRotatingFileHandler(
    "logs/RoomEye",
    encoding="utf-8",
    when="midnight",
    interval=1,
    backupCount=10,
)
h2.setLevel(logging.DEBUG)  # 出力レベルを設定
# フォーマッタを生成する
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# ハンドラーにフォーマッターを設定する
h1.setFormatter(fmt)
h2.setFormatter(fmt)
# ロガーにハンドラーを設定する
logger.addHandler(h1)
logger.addHandler(h2)


class RoomEye:
    LIGHT_OFF = 0
    LIGHT_ON = 1
    LIGHT_OFF_LIEDOWN = 2

    def __init__(self) -> None:
        self._human_detector = HumanDetector()
        # self._cap = cv2.VideoCapture(self._human_detector.getInput())
        # self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # カメラバッファを1にすることでレスポンスを上げる
        num_cam = 1
        self._image_a = None
        self._success_a = False
        t1 = threading.Thread(
            target=self.capMjpegStreamer, name="capMjpegStreamer", daemon=True
        )
        t1.start()

        if ENABLE_SECOND_CAMERA:
            self._human_detector2 = HumanDetector()
            self.__capB = cv2.VideoCapture(self._human_detector.getInput())
            self.__capB.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # カメラバッファを1にすることでレスポンスを上げる
            num_cam += 1

        self.__cvFpsCalc = CvFpsCalc(buffer_len=10)

        if ENABLE_LIEDOWN:
            self.__lieDownDetector = LieDownDetector(num_cam)

        # 環境変数を読み込む
        load_dotenv()
        self.__NATURE_REMO_TOKEN = os.environ.get(
            "NATURE_REMO_TOKEN", "XXXXXXXXXXX Your Nature Remo Token XXXXXXXXXX"
        )
        self.__ROOM_LIGHT_NAME = os.environ.get("ROOM_LIGHT_NAME", "Your Light Name")
        # NatureRemoに接続
        self.__remo = NatureRemoController(self.__NATURE_REMO_TOKEN)

        self._b_illumination = self.LIGHT_OFF
        self._lie_down_cnt = 0
        self._person_cnt = 0
        self._no_person_cnt = 0
        self._no_person_start = 0
        self._detect_image = None

    def lightOn(self):
        # self.__remo.sendOnSignalAilab(self.__ROOM_LIGHT_NAME)
        self.__remo.sendOnSignalLight(self.__ROOM_LIGHT_NAME)
        if self._detect_image is not None:
            # filename = os.getcwd() + '/img_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '_lightOn.jpg'
            filename = (
                "../logs/img/img_"
                + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                + "_lightOn.jpg"
            )
            ret = cv2.imwrite(filename, self._detect_image)
            logger.info("lightOn(): Save Image " + str(ret) + ", " + filename)

    def lightOff(self):
        # self.__remo.sendOffSignalAilab(self.__ROOM_LIGHT_NAME, 2)
        self.__remo.sendOffSignalLight(self.__ROOM_LIGHT_NAME)
        if self._detect_image is not None:
            filename = (
                "../logs/img/img_"
                + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                + "_lightOff.jpg"
            )
            ret = cv2.imwrite(filename, self._detect_image)
            logger.info("lightOff(): Save Image " + str(ret) + ", " + filename)

    def isPerson(self):
        return (
            self._human_detector.isPerson() > 0
            or (ENABLE_SECOND_CAMERA and self._human_detector2.isPerson() > 0)
            # self.__lieDownDetector.isPerson()
        )

    def isLieDown(self):
        return (
            ENABLE_LIEDOWN
            and self.__lieDownDetector.isLieDown()
            and not self.__lieDownDetector.isWakeUp()
        ) and (ENABLE_SECOND_CAMERA and not self._human_detector2.isPerson() > 0)

    def isWakeUp(self):
        return (ENABLE_LIEDOWN and self.__lieDownDetector.isWakeUp()) or (
            ENABLE_SECOND_CAMERA and self._human_detector2.isPerson() > 0
        )

    def capMjpegStreamer(self):
        # mjpg-streamerを動作させているPC・ポートを入力
        URL = "http://192.168.0.130:8080/?action=stream"
        while True:
            self._cap = cv2.VideoCapture(URL)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # カメラバッファを1にすることでレスポンスを上げる
            self._image_a = None
            self._success_a = False
            while self._cap.isOpened():
                self._success_a, self._image_a = self._cap.read()
                if not self._success_a:
                    logger.error("Ignoring empty camera frame mjpeg-streamer.")
                    self._cap.release()
                    break
                time.sleep(0.05)
            logger.error("capMjpegStreamer(): Reconnect VideoCapture.")
            time.sleep(3)

    def applianceControl(self):
        if self._b_illumination == self.LIGHT_ON:
            if self.isPerson() or (
                ENABLE_LIEDOWN and self.__lieDownDetector.isPerson()
            ):
                self._no_person_cnt = 0
                if self.isLieDown():
                    self._lie_down_cnt += 1
                    if self._lie_down_cnt >= LIE_DOWN_CNT_THREASHOLD:
                        logger.info("Lie down !!")
                        self.lightOff()
                        self._b_illumination = self.LIGHT_OFF_LIEDOWN
                        self._lie_down_cnt = 0
                    else:
                        logger.info("lieDownCnt = %d", self._lie_down_cnt)
                else:
                    self._lie_down_cnt = 0
            else:
                if self._no_person_cnt == 0:
                    self._no_person_start = time.time()
                self._no_person_cnt += 1
                if time.time() - self._no_person_start >= NO_PERSON_TIME_THREASHOLD:
                    logger.info("Light Off!!")
                    self.lightOff()
                    self._b_illumination = self.LIGHT_OFF
                    self._no_person_cnt = 0
                else:
                    logger.info(
                        "noPersonCnt = %d, noPersonTime = %s",
                        self._no_person_cnt,
                        format(time.time() - self._no_person_start, ".2f"),
                    )

        elif self._b_illumination == self.LIGHT_OFF:
            if self.isPerson():
                self._person_cnt += 1
                if self._person_cnt >= PERSON_CNT_THREASHOLD:
                    logger.info("Light On!!")
                    self.lightOn()
                    self._b_illumination = self.LIGHT_ON
                    self._person_cnt = 0
                else:
                    logger.info("personCnt = %d", self._person_cnt)
            else:
                self._person_cnt = 0

        elif self._b_illumination == self.LIGHT_OFF_LIEDOWN:
            if self.isWakeUp():
                self._person_cnt += 1
                if self._person_cnt >= PERSON_CNT_THREASHOLD:
                    logger.info("Light On!!")
                    self.lightOn()
                    self._b_illumination = self.LIGHT_ON
                    self._person_cnt = 0
                else:
                    logger.info("personCnt = %d", self._person_cnt)
            else:
                self._person_cnt = 0

    def getBlankHW(self, height, width):
        return np.zeros((height, width, 3), np.uint8)

    def getBlank(self, image):
        height, width = image.shape[:2]
        return self.getBlankHW(height, width)

    def trimImage(self, image, left, top, right, bottom, keepSize=False):
        """
        指定されたサイズに画像を切り取る

        Args:
            image (_type_): 画像
            left (int): 左側
            top (int): 上側
            right (int): 右側
            bottom (int): 下側
            keepSize (bool, optional): True:サイズをキープして黒埋めする. Defaults to False.

        Returns:
            _type_: 切り取った画像
        """
        img = image[top:bottom, left:right]
        if keepSize:
            blank = self.getBlank(image)
            blank[top:bottom, left:right] = img
            return blank
        else:
            return img

    def procCamA(self):
        display_fps = self.__cvFpsCalc.get()
        if not self._success_a:
            logger.error("Ignoring empty camera frame A.")
            return None, None

        self._success_a = False
        # 画像の反転と回転
        if CAMERA_FLIP is not None:
            image = cv2.flip(self._image_a, CAMERA_FLIP)
        if CAMERA_ROTATE is not None:
            image = cv2.rotate(self._image_a, CAMERA_ROTATE)

        # 人検知
        darknet_img = self.trimImage(image, 180, 30, 500, 370, False)
        image1, person_images = self._human_detector.detect(darknet_img)
        # FPS表示
        fps_color = (0, 255, 0)
        cv2.putText(
            image1,
            "FPS:" + str(display_fps),
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            fps_color,
            2,
            cv2.LINE_AA,
        )

        # 寝ころび検知
        if ENABLE_LIEDOWN:
            # if len(person_images) == 0:
            #   person_images.append(image)
            # mediapipeImgs = [self.trimImage(image, 220, 90, 480, 310, False),
            mediapipeImgs = [darknet_img, self.getBlank(darknet_img)]
            # self.getBlank(imageB)]
            if len(person_images) > 0:
                mediapipeImgs[1] = person_images[0]
            # if len(person_images2) > 0:
            #  mediapipeImgs[2] = person_images2[0]
            images2 = self.__lieDownDetector.detects(mediapipeImgs)
        else:
            images2 = []

        return image1, images2

    def procCamB(self):
        successB, imageB = self.__capB.read()
        if not successB:
            logger.error("Ignoring empty camera frame B.")
            return None
        # imageB = cv2.rotate(imageB, cv2.ROTATE_90_CLOCKWISE)
        image_b1, person_images2 = self._human_detector2.detect(imageB)
        return image_b1

    def imShow(self, image1, images2=None, image_b1=None):
        detect_image_tile = []
        line1 = [image1]
        if image_b1 is not None:
            line1.append(image_b1)
        detect_image_tile.append(line1)
        if images2 is not None and len(images2) > 0:
            line2 = []
            for index, img in enumerate(images2):
                line2.append(img)
            line2.append(np.zeros((320, 240, 3), np.uint8))
            detect_image_tile.append(line2)
        self._detect_image = concat_tile_resize(detect_image_tile)
        cv2.imshow("detectImage", self._detect_image)

    def run(self):
        while True:
            while not self._success_a:
                time.sleep(0.1)
            image1, images2 = self.procCamA()
            if image1 is None:
                continue
            if ENABLE_SECOND_CAMERA:
                image_b1 = self.procCamB()
            else:
                image_b1 = None

            # 画像の表示
            self.imShow(image1, images2, image_b1)

            # 家電の操作
            self.applianceControl()

            if cv2.waitKey(5) & 0xFF == 27:
                break

            # 省エネのためスリープを入れる
            time.sleep(0.2)

        self._cap.release()
        cv2.destroyAllWindows()

    def release(self):
        self._cap.release()


def vconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    w_min = min(im.shape[1] for im in im_list)
    im_list_resize = [
        cv2.resize(
            im,
            (w_min, int(im.shape[0] * w_min / im.shape[1])),
            interpolation=interpolation,
        )
        for im in im_list
    ]
    return cv2.vconcat(im_list_resize)


def hconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    h_min = min(im.shape[0] for im in im_list)
    im_list_resize = [
        cv2.resize(
            im,
            (int(im.shape[1] * h_min / im.shape[0]), h_min),
            interpolation=interpolation,
        )
        for im in im_list
    ]
    return cv2.hconcat(im_list_resize)


def concat_tile_resize(im_list_2d, interpolation=cv2.INTER_CUBIC):
    im_list_v = [
        hconcat_resize_min(im_list_h, interpolation=cv2.INTER_CUBIC)
        for im_list_h in im_list_2d
    ]
    return vconcat_resize_min(im_list_v, interpolation=cv2.INTER_CUBIC)


if __name__ == "__main__":
    RoomEye = RoomEye()
    try:
        RoomEye.run()
    except:  # noqa: E722
        RoomEye.release()
        cv2.destroyAllWindows()
        logger.error(traceback.format_exc())
