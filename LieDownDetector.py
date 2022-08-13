import cv2
import mediapipe as mp
import math

import config

from logging import getLogger
logger = getLogger("RoomEye").getChild("LieDownDetector")

class LieDownDetector:
  """
  寝ころび検知クラス
  """

  def __init__(self) -> None:

    self.__mpDrawing = mp.solutions.drawing_utils
    #self.__mpHolistic = mp.solutions.holistic
    #self.__holistic = self.__mpHolistic.Holistic(
    #    min_detection_confidence=0.5,
    #    min_tracking_confidence=0.5)
    self.__mpPose = mp.solutions.pose
    self.__pose = self.__mpPose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)
    self.__results = None
    self.__bLieDown = False
    self.__bWakeUp = False

  def isLieDown(self):
    return self.__bLieDown

  def isWakeUp(self):
    return self.__bWakeUp

  def isPerson(self):
    return self.__bLieDown or self.__bWakeUp

  def calcBodyAngle(self, results):
    landmarkRightShoulder = None
    landmarkLeftShoulder = None
    landmarkRightHip = None
    landmarkLeftHip = None
    for index, landmark in enumerate(results.pose_landmarks.landmark):
      if index == 11:  # 右肩
        landmarkRightShoulder = landmark
      if index == 12:  # 左肩
        landmarkLeftShoulder = landmark
      if index == 23:  # 腰(右側)
        landmarkRightHip = landmark
      if index == 24:  # 腰(左側)
        landmarkLeftHip = landmark

    if (landmarkRightShoulder == None or landmarkLeftShoulder == None or
            landmarkRightHip == None or landmarkLeftHip == None):
      return None

    shoulderX = (landmarkRightShoulder.x + landmarkLeftShoulder.x) / 2
    shoulderY = (landmarkRightShoulder.y + landmarkLeftShoulder.y) / 2
    hipX = (landmarkRightHip.x + landmarkLeftHip.x) / 2
    hipY = (landmarkRightHip.y + landmarkLeftHip.y) / 2
    bodyAngle = math.degrees(math.atan2(hipY - shoulderY, shoulderX - hipX))
    #logger.debug("deltaX = " + format(shoulderX - hipX, ".2f") + ", deltaY = " + format(hipY - shoulderY, ".2f") + ", bodyAngle = " + format(bodyAngle, ".2f"))
    return bodyAngle

  def checkLieDown(self):
    if self.__results.pose_landmarks == None:
      return None, None

    minAngle1 = config.LIE_DOWN_ANGLE - config.LIE_DOWN_ANGLE_RANGE
    maxAngle1 = config.LIE_DOWN_ANGLE + config.LIE_DOWN_ANGLE_RANGE
    minAngle2 = minAngle1 + 180
    maxAngle2 = maxAngle1 - 180

    bodyAngle = self.calcBodyAngle(self.__results)
    if bodyAngle == None:
      return None, None
    elif (
        (bodyAngle >= minAngle1 and bodyAngle <= maxAngle1) or
        (bodyAngle >= minAngle2 or bodyAngle <= maxAngle2)
    ):
      return True, bodyAngle
    else:
      return False, bodyAngle

  def detect(self, flame):
    # Flip the image horizontally for a later selfie-view display, and convert
    # the BGR image to RGB.
    image = cv2.cvtColor(flame, cv2.COLOR_BGR2RGB)

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    #self.__results = self.__holistic.process(image)
    self.__results = self.__pose.process(image)

    # Draw landmark annotation on the image.
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    #self.__mpDrawing.draw_landmarks(
    #    image, self.__results.face_landmarks, self.__mpHolistic.FACE_CONNECTIONS)
    #self.__mpDrawing.draw_landmarks(
    #    image, self.__results.left_hand_landmarks, self.__mpHolistic.HAND_CONNECTIONS)
    #self.__mpDrawing.draw_landmarks(
    #    image, self.__results.right_hand_landmarks, self.__mpHolistic.HAND_CONNECTIONS)
    #self.__mpDrawing.draw_landmarks(
    #    image, self.__results.pose_landmarks, self.__mpHolistic.POSE_CONNECTIONS)
    self.__mpDrawing.draw_landmarks(
        image, self.__results.pose_landmarks, self.__mpPose.POSE_CONNECTIONS)

    return image

  def detects(self, flames):
    if len(flames) == 0:
      return []

    self.__bLieDown = False
    self.__bWakeUp = False
    images = []
    for flame in flames:
      image = self.detect(flame)
      bLieDown, bodyAngle = self.checkLieDown()
      if bodyAngle != None:
        cv2.putText(image, "bodyAngle:" + '{:.1f}'.format(bodyAngle), (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
      images.append(image)
      if bLieDown == True:
        self.__bLieDown = True
      elif bLieDown == False:
        self.__bWakeUp = True

    return images
