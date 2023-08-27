import cv2
from collections import deque


class CvFpsCalc(object):
  """フレームレートを計算する

  Args:
      object (_type_): _description_
  """

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
