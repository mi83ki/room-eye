import cv2
from HumanDetector import HumanDetector

from applianceController.method1_Login.NatureRemoController import NatureRemoController
import myToken

from CvFpsCalc import CvFpsCalc
from LieDownDetector import LieDownDetector

from darknet import darknet
import argparse
import os
import random
import time

# 人を検知したと判定する繰り返し回数
PERSON_CNT_THREASHOLD = 3
# 寝ころんだと判定する繰り返し回数
LIE_DOWN_CNT_THREASHOLD = 3
# 人がいなくなったと判定する繰り返し回数
NO_PERSON_CNT_THREASHOLD = 20

class HomeEye:
  def __init__(self) -> None:
    self.__humanDetector = HumanDetector()
    self.__cap = cv2.VideoCapture(self.__humanDetector.getInput())
    self.__cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)    # カメラバッファを1にすることでレスポンスを上げる
    self.__cvFpsCalc = CvFpsCalc(buffer_len=10)
    self.__lieDownDetector = LieDownDetector()

    # NatureRemoに接続
    self.__remo = NatureRemoController('Remo', myToken.default)
    self.__bIllumination = False
    self.__lieDownCnt = 0
    self.__personCnt = 0
    self.__noPersonCnt = 0

  def applianceControl(self):
    if self.__bIllumination:
      if self.__humanDetector.isPerson() > 0 or self.__lieDownDetector.isPerson():
        self.__noPersonCnt = 0
        if self.__lieDownDetector.isLieDown():
          self.__lieDownCnt += 1
          if self.__lieDownCnt >= LIE_DOWN_CNT_THREASHOLD:
            print("Lie down !!")
            #self.__remo.sendOffSignalAilab('ailabキッチン照明', 2)
            self.__remo.sendOffSignal('書斎')
            self.__bIllumination = False
            self.__lieDownCnt = 0
          else:
            print("lieDownCnt = " + str(self.__lieDownCnt))
        else:
          self.__lieDownCnt = 0
      else:
        self.__noPersonCnt += 1
        if self.__noPersonCnt >= NO_PERSON_CNT_THREASHOLD:
          print("Light Off!!")
          #self.__remo.sendOffSignalAilab('ailabキッチン照明', 2)
          self.__remo.sendOffSignal('書斎')
          self.__bIllumination = False
          self.__noPersonCnt = 0
        else:
          print("noPersonCnt = " + str(self.__noPersonCnt))
    else:
      if self.__humanDetector.isPerson() > 0 or self.__lieDownDetector.isPerson():
        if not self.__lieDownDetector.isLieDown():
          self.__personCnt += 1
          if self.__personCnt >= PERSON_CNT_THREASHOLD:
            print("Light On!!")
            # self.__remo.sendOnSignalAilab('ailabキッチン照明')
            self.__remo.sendOnSignal('書斎')
            self.__bIllumination = True
            self.__personCnt = 0
          else:
            print("personCnt = " + str(self.__personCnt))
        else:
          self.__personCnt = 0

  def run(self):
    while self.__cap.isOpened():
      display_fps = self.__cvFpsCalc.get()
      success, image = self.__cap.read()
      if not success:
        print("Ignoring empty camera frame.")
        # If loading a video, use 'break' instead of 'continue'.
        continue

      # 人検知
      image1 = self.__humanDetector.detect(image)
      # 寝ころび検知
      image2 = self.__lieDownDetector.detect(image)
      # 家電の操作
      self.applianceControl()

      # FPS表示
      fps_color = (0, 255, 0)
      cv2.putText(image2, "FPS:" + str(display_fps), (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, fps_color, 2, cv2.LINE_AA)

      cv2.imshow('Inference', image1)
      cv2.imshow('MediaPipe Holistic', image2)
      if cv2.waitKey(5) & 0xFF == 27:
        break

      # 省エネのためスリープを入れる
      time.sleep(0.3)

    self.__cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
  HomeEye = HomeEye()
  HomeEye.run()
