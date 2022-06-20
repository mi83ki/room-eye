import cv2

from applianceController.method1_Login.NatureRemoController import NatureRemoController
import myToken

from CvFpsCalc import CvFpsCalc
from LieDownDetector import LieDownDetector

from darknet import darknet
import argparse
import os
import random
import time


class RoomController:
  def __init__(self) -> None:
    self.__cap = cv2.VideoCapture(0)
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
      if self.__lieDownDetector.isPerson():
        self.__noPersonCnt = 0
        if self.__lieDownDetector.isLieDown():
          self.__lieDownCnt += 1
          if self.__lieDownCnt >= 10:
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
        if self.__noPersonCnt >= 10:
          print("Light Off!!")
          #self.__remo.sendOffSignalAilab('ailabキッチン照明', 2)
          self.__remo.sendOffSignal('書斎')
          self.__bIllumination = False
          self.__noPersonCnt = 0
        else:
          print("noPersonCnt = " + str(self.__noPersonCnt))
    else:
      if self.__lieDownDetector.isPerson():
        if not self.__lieDownDetector.isLieDown():
          self.__personCnt += 1
          if self.__personCnt >= 10:
            print("Light On!!")
            #self.__remo.sendOnSignalAilab('ailabキッチン照明')
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

      # Flip the image horizontally for a later selfie-view display, and convert
      # the BGR image to RGB.
      image = cv2.cvtColor(cv2.flip(image, -1), cv2.COLOR_BGR2RGB)

      # 寝ころび検知
      image = self.__lieDownDetector.detect(image)
      self.applianceControl()

      # FPS表示
      fps_color = (0, 255, 0)
      cv2.putText(image, "FPS:" + str(display_fps), (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, fps_color, 2, cv2.LINE_AA)

      cv2.imshow('MediaPipe Holistic', image)
      if cv2.waitKey(5) & 0xFF == 27:
        break

      # 省エネのためスリープを入れる
      time.sleep(0.4)

    self.__cap.release()


if __name__ == "__main__":
  roomController = RoomController()
  roomController.run()
