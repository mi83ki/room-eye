import argparse
import os
from logging import getLogger

import cv2
import numpy as np

import config
from darknet import darknet

logger = getLogger("RoomEye").getChild("HD")


class HumanDetector:
    """
    人検知判定クラス
    """

    def __init__(self) -> None:
        # darknetのディレクトリに移動する
        darknetDir = os.path.dirname(os.path.abspath(__file__)) + "/darknet"
        os.chdir(darknetDir)

        self.__args = self.parser()
        self.check_arguments_errors(self.__args)
        self.__network, self.__class_names, self.__class_colors = darknet.load_network(
            self.__args.config_file, self.__args.data_file, self.__args.weights, batch_size=1
        )
        self.__darknetWidth = darknet.network_width(self.__network)
        self.__darknetHeight = darknet.network_height(self.__network)
        self.__darknet_image = darknet.make_image(self.__darknetWidth, self.__darknetHeight, 3)
        self.__personImages = []
        logger.info("HumanDetector start")

    def parser(self):
        parser = argparse.ArgumentParser(description="YOLO Object Detection")
        parser.add_argument(
            "--input", type=str, default="/dev/video0", help="video source. If empty, uses webcam 0 stream"
        )
        parser.add_argument("--weights", default="./yolov4-tiny.weights", help="yolo weights path")
        parser.add_argument("--dont_show", action="store_true", help="windown inference display. For headless systems")
        parser.add_argument("--ext_output", action="store_true", help="display bbox coordinates of detected objects")
        parser.add_argument("--config_file", default="./cfg/yolov4-tiny.cfg", help="path to config file")
        parser.add_argument("--data_file", default="./cfg/coco.data", help="path to data file")
        parser.add_argument(
            "--thresh", type=float, default=0.25, help="remove detections with confidence below this value"
        )
        return parser.parse_args()

    def str2int(self, video_path):
        """
        argparse returns and string althout webcam uses int (0, 1 ...)
        Cast to int if needed
        """
        try:
            return int(video_path)
        except ValueError:
            return video_path

    def getInput(self):
        return self.str2int(self.__args.input)

    def check_arguments_errors(self, args):
        assert 0 < args.thresh < 1, "Threshold should be a float between zero and one (non-inclusive)"
        if not os.path.exists(args.config_file):
            raise (ValueError("Invalid config path {}".format(os.path.abspath(args.config_file))))
        if not os.path.exists(args.weights):
            raise (ValueError("Invalid weight path {}".format(os.path.abspath(args.weights))))
        if not os.path.exists(args.data_file):
            raise (ValueError("Invalid data file path {}".format(os.path.abspath(args.data_file))))
        if self.str2int(args.input) == str and not os.path.exists(args.input):
            raise (ValueError("Invalid video path {}".format(os.path.abspath(args.input))))

    def set_saved_video(self, input_video, output_video, size):
        fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
        # fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        fps = int(input_video.get(cv2.CAP_PROP_FPS))
        video = cv2.VideoWriter(output_video, fourcc, fps, size)
        return video

    def getImages(self, image, detections, _label):
        # 画像の大きさを取得
        height, width = image.shape[:2]
        images = []
        for label, confidence, bbox in detections:
            if label == _label:
                left, top, right, bottom = darknet.bbox2points(bbox)
                img = image[top:bottom, left:right]
                blank = np.zeros((height, width, 3), np.uint8)
                blank[top:bottom, left:right] = img
                images.append(blank)
        return images

    def convert2relative(self, bbox):
        """
        YOLO format use relative coordinates for annotation
        """
        x, y, w, h = bbox
        _height = self.__darknetHeight
        _width = self.__darknetWidth
        return x / _width, y / _height, w / _width, h / _height

    def convert2original(self, image, bbox):
        x, y, w, h = self.convert2relative(bbox)

        image_h, image_w, __ = image.shape

        orig_x = int(x * image_w)
        orig_y = int(y * image_h)
        orig_width = int(w * image_w)
        orig_height = int(h * image_h)

        bbox_converted = (orig_x, orig_y, orig_width, orig_height)

        return bbox_converted

    def image_detection(self, image, network, class_names, class_colors, thresh, width, height):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_resized = cv2.resize(image_rgb, (width, height), interpolation=cv2.INTER_LINEAR)

        darknet.copy_image_from_bytes(self.__darknet_image, image_resized.tobytes())
        detections = darknet.detect_image(network, class_names, self.__darknet_image, thresh=thresh)
        detections_adjusted = []
        for label, confidence, bbox in detections:
            bbox_adjusted = self.convert2original(image, bbox)
            detections_adjusted.append((str(label), confidence, bbox_adjusted))
        outImage = darknet.draw_boxes(detections_adjusted, image.copy(), class_colors)
        personImages = self.getImages(image, detections_adjusted, "person")
        return outImage, personImages, detections

    def isPerson(self):
        personCnt = 0
        for label, confidence, bbox in self.__detections:
            if label == "person":
                if float(confidence) > config.DETECT_THREASHOLD:
                    personCnt += 1
                x, y, w, h = self.convert2relative(bbox)
                logger.debug(
                    "isPerson(): pCnt = "
                    + str(personCnt)
                    + ", conf = "
                    + str(confidence)
                    + ", bbox = ("
                    + format(x, ".2f")
                    + ", "
                    + format(y, ".2f")
                    + ", "
                    + format(w, ".2f")
                    + ", "
                    + format(h, ".2f")
                    + ")"
                )
        return personCnt

    def detect(self, flame):
        image, personImages, self.__detections = self.image_detection(
            flame,
            self.__network,
            self.__class_names,
            self.__class_colors,
            self.__args.thresh,
            self.__darknetWidth,
            self.__darknetHeight,
        )
        return image, personImages
