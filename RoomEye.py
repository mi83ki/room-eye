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
from dotenv import load_dotenv

from config import (CAMERA_FLIP, CAMERA_ROTATE, ENABLE_LIEDOWN,
                    ENABLE_SECOND_CAMERA, LIE_DOWN_CNT_THREASHOLD,
                    NO_PERSON_TIME_THREASHOLD, PERSON_CNT_THREASHOLD)
from CvFpsCalc import CvFpsCalc
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
        self.__humanDetector = HumanDetector()
        # self.__cap = cv2.VideoCapture(self.__humanDetector.getInput())
        # mjpg-streamerを動作させているPC・ポートを入力
        URL = "http://192.168.0.130:8080/?action=stream"
        self.__cap = cv2.VideoCapture(URL)
        self.__cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # カメラバッファを1にすることでレスポンスを上げる
        numCam = 1
        self.__imageA = None
        self.__successA = False
        t1 = threading.Thread(target=self.capMjpegStreamer, name="capMjpegStreamer")
        t1.setDaemon(True)
        t1.start()

        if ENABLE_SECOND_CAMERA:
            self.__humanDetector2 = HumanDetector()
            self.__capB = cv2.VideoCapture(self.__humanDetector.getInput())
            self.__capB.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # カメラバッファを1にすることでレスポンスを上げる
            numCam += 1

        self.__cvFpsCalc = CvFpsCalc(buffer_len=10)

        if ENABLE_LIEDOWN:
            self.__lieDownDetector = LieDownDetector(numCam)

        # 環境変数を読み込む
        load_dotenv()
        self.__NATURE_REMO_TOKEN = os.environ.get("NATURE_REMO_TOKEN", "XXXXXXXXXXX Your Nature Remo Token XXXXXXXXXX")
        self.__ROOM_LIGHT_NAME = os.environ.get("ROOM_LIGHT_NAME", "Your Light Name")
        # NatureRemoに接続
        self.__remo = NatureRemoController(self.__NATURE_REMO_TOKEN)

        self.__bIllumination = self.LIGHT_OFF
        self.__lieDownCnt = 0
        self.__personCnt = 0
        self.__noPersonCnt = 0
        self.__noPersonStart = 0
        self.__detectImage = None

    def lightOn(self):
        # self.__remo.sendOnSignalAilab(self.__ROOM_LIGHT_NAME)
        self.__remo.sendOnSignalLight(self.__ROOM_LIGHT_NAME)
        if self.__detectImage is not None:
            # filename = os.getcwd() + '/img_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '_lightOn.jpg'
            filename = "../logs/img/img_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_lightOn.jpg"
            ret = cv2.imwrite(filename, self.__detectImage)
            logger.info("lightOn(): Save Image " + str(ret) + ", " + filename)

    def lightOff(self):
        # self.__remo.sendOffSignalAilab(self.__ROOM_LIGHT_NAME, 2)
        self.__remo.sendOffSignalLight(self.__ROOM_LIGHT_NAME)
        if self.__detectImage is not None:
            filename = "../logs/img/img_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_lightOff.jpg"
            ret = cv2.imwrite(filename, self.__detectImage)
            logger.info("lightOff(): Save Image " + str(ret) + ", " + filename)

    def isPerson(self):
        return (
            self.__humanDetector.isPerson() > 0
            or (ENABLE_SECOND_CAMERA and self.__humanDetector2.isPerson() > 0)
            # self.__lieDownDetector.isPerson()
        )

    def isLieDown(self):
        return (ENABLE_LIEDOWN and self.__lieDownDetector.isLieDown() and not self.__lieDownDetector.isWakeUp()) and (
            ENABLE_SECOND_CAMERA and not self.__humanDetector2.isPerson() > 0
        )

    def isWakeUp(self):
        return (ENABLE_LIEDOWN and self.__lieDownDetector.isWakeUp()) or (
            ENABLE_SECOND_CAMERA and self.__humanDetector2.isPerson() > 0
        )

    def capMjpegStreamer(self):
        while self.__cap.isOpened():
            self.__successA, self.__imageA = self.__cap.read()
            if not self.__successA:
                logger.error("Ignoring empty camera frame mjpeg-streamer.")
                break
            time.sleep(0.05)
        pass

    def applianceControl(self):
        if self.__bIllumination == self.LIGHT_ON:
            if self.isPerson() or (ENABLE_LIEDOWN and self.__lieDownDetector.isPerson()):
                self.__noPersonCnt = 0
                if self.isLieDown():
                    self.__lieDownCnt += 1
                    if self.__lieDownCnt >= LIE_DOWN_CNT_THREASHOLD:
                        logger.info("Lie down !!")
                        self.lightOff()
                        self.__bIllumination = self.LIGHT_OFF_LIEDOWN
                        self.__lieDownCnt = 0
                    else:
                        logger.info("lieDownCnt = " + str(self.__lieDownCnt))
                else:
                    self.__lieDownCnt = 0
            else:
                if self.__noPersonCnt == 0:
                    self.__noPersonStart = time.time()
                self.__noPersonCnt += 1
                if time.time() - self.__noPersonStart >= NO_PERSON_TIME_THREASHOLD:
                    logger.info("Light Off!!")
                    self.lightOff()
                    self.__bIllumination = self.LIGHT_OFF
                    self.__noPersonCnt = 0
                else:
                    logger.info(
                        "noPersonCnt = "
                        + str(self.__noPersonCnt)
                        + ", noPersonTime = "
                        + format(time.time() - self.__noPersonStart, ".2f")
                    )

        elif self.__bIllumination == self.LIGHT_OFF:
            if self.isPerson():
                self.__personCnt += 1
                if self.__personCnt >= PERSON_CNT_THREASHOLD:
                    logger.info("Light On!!")
                    self.lightOn()
                    self.__bIllumination = self.LIGHT_ON
                    self.__personCnt = 0
                else:
                    logger.info("personCnt = " + str(self.__personCnt))
            else:
                self.__personCnt = 0

        elif self.__bIllumination == self.LIGHT_OFF_LIEDOWN:
            if self.isWakeUp():
                self.__personCnt += 1
                if self.__personCnt >= PERSON_CNT_THREASHOLD:
                    logger.info("Light On!!")
                    self.lightOn()
                    self.__bIllumination = self.LIGHT_ON
                    self.__personCnt = 0
                else:
                    logger.info("personCnt = " + str(self.__personCnt))
            else:
                self.__personCnt = 0

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
        if not self.__successA:
            logger.error("Ignoring empty camera frame A.")
            return None, None

        self.__successA = False
        # 画像の反転と回転
        if CAMERA_FLIP is not None:
            image = cv2.flip(self.__imageA, CAMERA_FLIP)
        if CAMERA_ROTATE is not None:
            image = cv2.rotate(self.__imageA, CAMERA_ROTATE)

        # 人検知
        darknetImg = self.trimImage(image, 180, 30, 500, 370, False)
        image1, personImages = self.__humanDetector.detect(darknetImg)
        # FPS表示
        fps_color = (0, 255, 0)
        cv2.putText(
            image1, "FPS:" + str(display_fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, fps_color, 2, cv2.LINE_AA
        )

        # 寝ころび検知
        if ENABLE_LIEDOWN:
            # if len(personImages) == 0:
            #   personImages.append(image)
            # mediapipeImgs = [self.trimImage(image, 220, 90, 480, 310, False),
            mediapipeImgs = [darknetImg, self.getBlank(darknetImg)]
            # self.getBlank(imageB)]
            if len(personImages) > 0:
                mediapipeImgs[1] = personImages[0]
            # if len(personImages2) > 0:
            #  mediapipeImgs[2] = personImages2[0]
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
        imageB1, personImages2 = self.__humanDetector2.detect(imageB)
        return imageB1

    def imShow(self, image1, images2=None, imageB1=None):
        detectImageTile = []
        line1 = [image1]
        if imageB1 is not None:
            line1.append(imageB1)
        detectImageTile.append(line1)
        if images2 is not None and len(images2) > 0:
            line2 = []
            for index, img in enumerate(images2):
                line2.append(img)
            line2.append(np.zeros((320, 240, 3), np.uint8))
            detectImageTile.append(line2)
        self.__detectImage = concat_tile_resize(detectImageTile)
        cv2.imshow("detectImage", self.__detectImage)

    def run(self):
        while True:
            while not self.__successA:
                time.sleep(0.1)
            image1, images2 = self.procCamA()
            if image1 is None:
                continue
            if ENABLE_SECOND_CAMERA:
                imageB1 = self.procCamB()
            else:
                imageB1 = None

            # 画像の表示
            self.imShow(image1, images2, imageB1)

            # 家電の操作
            self.applianceControl()

            if cv2.waitKey(5) & 0xFF == 27:
                break

            # 省エネのためスリープを入れる
            time.sleep(0.2)

        self.__cap.release()
        cv2.destroyAllWindows()

    def release(self):
        self.__cap.release()


def vconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    w_min = min(im.shape[1] for im in im_list)
    im_list_resize = [
        cv2.resize(im, (w_min, int(im.shape[0] * w_min / im.shape[1])), interpolation=interpolation) for im in im_list
    ]
    return cv2.vconcat(im_list_resize)


def hconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    h_min = min(im.shape[0] for im in im_list)
    im_list_resize = [
        cv2.resize(im, (int(im.shape[1] * h_min / im.shape[0]), h_min), interpolation=interpolation) for im in im_list
    ]
    return cv2.hconcat(im_list_resize)


def concat_tile_resize(im_list_2d, interpolation=cv2.INTER_CUBIC):
    im_list_v = [hconcat_resize_min(im_list_h, interpolation=cv2.INTER_CUBIC) for im_list_h in im_list_2d]
    return vconcat_resize_min(im_list_v, interpolation=cv2.INTER_CUBIC)


if __name__ == "__main__":
    RoomEye = RoomEye()
    try:
        RoomEye.run()
    except:
        RoomEye.release()
        cv2.destroyAllWindows()
        logger.error(traceback.format_exc())
