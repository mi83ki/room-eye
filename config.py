import cv2

# 人検知を判定するしきい値
DETECT_THREASHOLD = 0.30

# 寝ころびと判定する姿勢角[deg]
LIE_DOWN_ANGLE = 0
# 寝ころびと判定する姿勢角の余裕度（±）[deg]
LIE_DOWN_ANGLE_RANGE = 30

# 人を検知したと判定する繰り返し回数
PERSON_CNT_THREASHOLD = 2
# 寝ころんだと判定する繰り返し回数
LIE_DOWN_CNT_THREASHOLD = 5
# 人がいなくなってから照明を消すまでの時間
NO_PERSON_TIME_THREASHOLD = 5.0

# カメラを反転するかどうか
# None : 反転しない
# 0 : 上下反転
# -1 : 左右反転
# 1 : 上下左右反転
CAMERA_FLIP = None

# カメラを回転するかどうか
# None : 回転しない
# cv2.ROTATE_90_CLOCKWISE : 時計回りに90°回転
# cv2.ROTATE_90_COUNTERCLOCKWISE : 反時計回りに90°回転
# cv2.ROTATE_180 : 180°回転
# CAMERA_ROTATE = cv2.ROTATE_90_CLOCKWISE
CAMERA_ROTATE = cv2.ROTATE_180
