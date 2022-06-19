import cv2
import mediapipe as mp

from collections import deque

from applianceController.method1_Login.NatureRemoController import NatureRemoController
import myToken


class CvFpsCalc(object):
  def __init__(self, buffer_len=1):
    self._start_tick = cv2.getTickCount()
    self._freq = 1000.0 / cv2.getTickFrequency()
    self._difftimes = deque(maxlen=buffer_len)

  def get(self):
    current_tick = cv2.getTickCount()
    different_time = (current_tick - self._start_tick) * self._freq
    self._start_tick = current_tick

    self._difftimes.append(different_time)

    fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
    fps_rounded = round(fps, 2)

    return fps_rounded


class LieDownDetector:
  def __init__(self) -> None:
    # NatureRemoに接続
    self.__remo = NatureRemoController('Remo', myToken.default)
    self.__bIllumination = False
    self.__lieDownCnt = 0
    self.__personCnt = 0
    self.__noPersonCnt = 0

  def isPerson(self, pose_landmarks):
    return pose_landmarks != None

  def isLieDown(self, pose_landmarks):
    if pose_landmarks == None:
      return False

    landmarkRightShoulder = None
    landmarkLeftShoulder = None
    landmarkRightHip = None
    landmarkLeftHip = None
    for index, landmark in enumerate(pose_landmarks.landmark):
      if index == 11:  # 右肩
        landmarkRightShoulder = landmark
      if index == 12:  # 左肩
        landmarkLeftShoulder = landmark
      if index == 23:  # 腰(右側)
        landmarkRightHip = landmark
      if index == 24:  # 腰(左側)
        landmarkLeftHip = landmark

    lieDownR = False
    lieDownL = False
    if landmarkRightShoulder != None and landmarkRightHip != None:
      xdefR = abs(landmarkRightShoulder.x - landmarkRightHip.x)
      ydefR = abs(landmarkRightShoulder.y - landmarkRightHip.y)
      #print(str(xdefR) + ", " + str(ydefR))
      if xdefR > ydefR:
        lieDownR = True

    if landmarkLeftShoulder != None and landmarkLeftHip != None:
      xdefL = abs(landmarkLeftShoulder.x - landmarkLeftHip.x)
      ydefL = abs(landmarkLeftShoulder.y - landmarkLeftHip.y)
      #print(str(xdefL) + ", " + str(ydefL))
      if xdefL > ydefL:
        lieDownL = True
    #print("lieDownR = " + str(lieDownR) + ", lieDownL = " + str(lieDownL))
    return lieDownR and lieDownL

  def applianceControl(self, results):
    if self.__bIllumination:
      if self.isPerson(results.pose_landmarks):
        self.__noPersonCnt = 0
        if self.isLieDown(results.pose_landmarks):
          self.__lieDownCnt += 1
          if self.__lieDownCnt >= 10:
            print("Lie down !!")
            self.__remo.sendOffSignalAilab('ailabキッチン照明', 2)
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
          self.__remo.sendOffSignalAilab('ailabキッチン照明', 2)
          self.__bIllumination = False
          self.__noPersonCnt = 0
        else:
          print("noPersonCnt = " + str(self.__noPersonCnt))
    else:
      if self.isPerson(results.pose_landmarks):
        if not self.isLieDown(results.pose_landmarks):
          self.__personCnt += 1
          if self.__personCnt >= 10:
            print("Light On!!")
            self.__remo.sendOnSignalAilab('ailabキッチン照明')
            self.__bIllumination = True
            self.__personCnt = 0
          else:
            print("personCnt = " + str(self.__personCnt))
        else:
          self.__personCnt = 0


if __name__ == "__main__":
  mp_drawing = mp.solutions.drawing_utils
  mp_holistic = mp.solutions.holistic

  cap = cv2.VideoCapture(0)
  cvFpsCalc = CvFpsCalc(buffer_len=10)
  with mp_holistic.Holistic(
          min_detection_confidence=0.5,
          min_tracking_confidence=0.5) as holistic:

    lieDownDetector = LieDownDetector()

    while cap.isOpened():
      display_fps = cvFpsCalc.get()
      success, image = cap.read()
      if not success:
        print("Ignoring empty camera frame.")
        # If loading a video, use 'break' instead of 'continue'.
        continue

      # Flip the image horizontally for a later selfie-view display, and convert
      # the BGR image to RGB.
      image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
      # To improve performance, optionally mark the image as not writeable to
      # pass by reference.
      image.flags.writeable = False
      results = holistic.process(image)

      # 人検知、寝ころび検知
      lieDownDetector.applianceControl(results)

      # Draw landmark annotation on the image.
      image.flags.writeable = True
      image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
      mp_drawing.draw_landmarks(
          image, results.face_landmarks, mp_holistic.FACE_CONNECTIONS)
      mp_drawing.draw_landmarks(
          image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
      mp_drawing.draw_landmarks(
          image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
      mp_drawing.draw_landmarks(
          image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)

      # FPS表示
      fps_color = (0, 255, 0)
      cv2.putText(image, "FPS:" + str(display_fps), (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, fps_color, 2, cv2.LINE_AA)

      cv2.imshow('MediaPipe Holistic', image)
      if cv2.waitKey(5) & 0xFF == 27:
        break
  cap.release()
