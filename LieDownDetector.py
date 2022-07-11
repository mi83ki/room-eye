import cv2
import mediapipe as mp


class LieDownDetector:
  """
  寝ころび検知クラス
  """

  def __init__(self) -> None:

    self.__mpDrawing = mp.solutions.drawing_utils
    self.__mpHolistic = mp.solutions.holistic
    self.__holistic = self.__mpHolistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)
    self.__results = None

  def isPerson(self):
    return self.__results.pose_landmarks != None

  def isLieDown(self):
    if self.__results.pose_landmarks == None:
      return False

    landmarkRightShoulder = None
    landmarkLeftShoulder = None
    landmarkRightHip = None
    landmarkLeftHip = None
    for index, landmark in enumerate(self.__results.pose_landmarks.landmark):
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

  def detect(self, flame):
    # Flip the image horizontally for a later selfie-view display, and convert
    # the BGR image to RGB.
    image = cv2.cvtColor(cv2.flip(flame, -1), cv2.COLOR_BGR2RGB)

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    self.__results = self.__holistic.process(image)

    # Draw landmark annotation on the image.
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    self.__mpDrawing.draw_landmarks(
        image, self.__results.face_landmarks, self.__mpHolistic.FACE_CONNECTIONS)
    self.__mpDrawing.draw_landmarks(
        image, self.__results.left_hand_landmarks, self.__mpHolistic.HAND_CONNECTIONS)
    self.__mpDrawing.draw_landmarks(
        image, self.__results.right_hand_landmarks, self.__mpHolistic.HAND_CONNECTIONS)
    self.__mpDrawing.draw_landmarks(
        image, self.__results.pose_landmarks, self.__mpHolistic.POSE_CONNECTIONS)

    return image
