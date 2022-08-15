import cv2
import os
import time
from dotenv import load_dotenv
import traceback

import config
from HumanDetector import HumanDetector
from NatureRemoController.NatureRemoController import NatureRemoController
from CvFpsCalc import CvFpsCalc
from LieDownDetector import LieDownDetector

import logging
import logging.handlers
import os.path
# logsフォルダが無ければ作成する
if os.path.isdir("logs") == False:
  os.mkdir("logs")
# ロガーを取得する
logger = logging.getLogger("RoomEye")
logger.setLevel(logging.DEBUG)  # 出力レベルを設定
# ハンドラー1を生成する
h1 = logging.StreamHandler()
h1.setLevel(logging.DEBUG)  # 出力レベルを設定
# ハンドラー2を生成する
#h2 = logging.FileHandler('logs/RoomEye.log')
h2 = logging.handlers.TimedRotatingFileHandler(
    "logs/RoomEye", encoding='utf-8',
    when='midnight', interval=1, backupCount=10,
)
h2.setLevel(logging.DEBUG)  # 出力レベルを設定
# フォーマッタを生成する
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    self.__cap = cv2.VideoCapture(self.__humanDetector.getInput())
    self.__cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)    # カメラバッファを1にすることでレスポンスを上げる
    self.__cvFpsCalc = CvFpsCalc(buffer_len=10)
    self.__lieDownDetector = LieDownDetector()

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

  def lightOn(self):
    # self.__remo.sendOnSignalAilab(self.__ROOM_LIGHT_NAME)
    self.__remo.sendOnSignalLight(self.__ROOM_LIGHT_NAME)

  def lightOff(self):
    # self.__remo.sendOffSignalAilab(self.__ROOM_LIGHT_NAME, 2)
    self.__remo.sendOffSignalLight(self.__ROOM_LIGHT_NAME)

  def applianceControl(self):
    if self.__bIllumination == self.LIGHT_ON:
      if self.__humanDetector.isPerson() > 0 or self.__lieDownDetector.isPerson():
        self.__noPersonCnt = 0
        if self.__lieDownDetector.isLieDown() and not self.__lieDownDetector.isWakeUp():
          self.__lieDownCnt += 1
          if self.__lieDownCnt >= config.LIE_DOWN_CNT_THREASHOLD:
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
        if time.time() - self.__noPersonStart >= config.NO_PERSON_TIME_THREASHOLD:
          logger.info("Light Off!!")
          self.lightOff()
          self.__bIllumination = self.LIGHT_OFF
          self.__noPersonCnt = 0
        else:
          logger.info("noPersonCnt = " + str(self.__noPersonCnt) + ", noPersonTime = " + format(time.time() - self.__noPersonStart, ".2f"))

    elif self.__bIllumination == self.LIGHT_OFF:
      if self.__humanDetector.isPerson() > 0:
        self.__personCnt += 1
        if self.__personCnt >= config.PERSON_CNT_THREASHOLD:
          logger.info("Light On!!")
          self.lightOn()
          self.__bIllumination = self.LIGHT_ON
          self.__personCnt = 0
        else:
          logger.info("personCnt = " + str(self.__personCnt))
      else:
        self.__personCnt = 0

    elif self.__bIllumination == self.LIGHT_OFF_LIEDOWN:
      if self.__lieDownDetector.isWakeUp():
        self.__personCnt += 1
        if self.__personCnt >= config.PERSON_CNT_THREASHOLD:
          logger.info("Light On!!")
          self.lightOn()
          self.__bIllumination = self.LIGHT_ON
          self.__personCnt = 0
        else:
          logger.info("personCnt = " + str(self.__personCnt))
      else:
        self.__personCnt = 0

  def run(self):
    mediapipeWindows = []
    while self.__cap.isOpened():
      display_fps = self.__cvFpsCalc.get()
      success, image = self.__cap.read()
      if not success:
        logger.error("Ignoring empty camera frame.")
        # If loading a video, use 'break' instead of 'continue'.
        continue

      # 画像の反転と回転
      if config.CAMERA_FLIP is not None:
        image = cv2.flip(image, config.CAMERA_FLIP)
      if config.CAMERA_ROTATE is not None:
        image = cv2.rotate(image, config.CAMERA_ROTATE)

      # 人検知
      image1, personImages = self.__humanDetector.detect(image)
      # FPS表示
      fps_color = (0, 255, 0)
      cv2.putText(image1, "FPS:" + str(display_fps), (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, fps_color, 2, cv2.LINE_AA)
      cv2.imshow('Inference', image1)

      # 寝ころび検知
      if len(personImages) == 0:
        personImages.append(image)
      images2 = self.__lieDownDetector.detects(personImages)
      windows = []
      for index, img in enumerate(images2):
        windowName = 'MediaPipe Holistic ' + str(index)
        cv2.imshow(windowName, img)
        windows.append(windowName)
      # いらなくなったウインドウを閉じる
      for window in mediapipeWindows:
        if not window in windows:
          cv2.destroyWindow(window)
      mediapipeWindows = windows

      # 家電の操作
      self.applianceControl()

      if cv2.waitKey(5) & 0xFF == 27:
        break

      # 省エネのためスリープを入れる
      time.sleep(0.3)

    self.__cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
  RoomEye = RoomEye()
  try:
    RoomEye.run()
  except:
    logger.error(traceback.format_exc())
