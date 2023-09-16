"""人検知部

画像から人の有無を検出します

"""

import threading

import cv2
from ultralytics import YOLO


class HumanDetector:
    """人検知クラス"""

    def __init__(self) -> None:
        thread = threading.Thread(target=self.begin, daemon=True)
        thread.start()

    def begin(self) -> None:
        # Load the YOLOv8 model
        model = YOLO("weights/yolov8n.pt")

        # Open the video file
        cap = cv2.VideoCapture(0)

        # Loop through the video frames
        while cap.isOpened():
            # Read a frame from the video
            success, frame = cap.read()

            if success:
                # Run YOLOv8 inference on the frame
                results = model(frame)

                # Visualize the results on the frame
                annotated_frame = results[0].plot()

                # Display the annotated frame
                cv2.imshow("YOLOv8 Inference", annotated_frame)

                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                # Break the loop if the end of the video is reached
                break

        # Release the video capture object and close the display window
        cap.release()
        cv2.destroyAllWindows()
