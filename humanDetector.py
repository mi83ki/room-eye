import myToken
from applianceController.method1_Login.NatureRemoController import NatureRemoController
from darknet import darknet
import argparse
import os
import random
import time
import cv2

# darknetのディレクトリに移動する
darknetDir = os.path.dirname(os.path.abspath(__file__)) + "/darknet"
os.chdir(darknetDir)


def parser():
    parser = argparse.ArgumentParser(description="YOLO Object Detection")
    parser.add_argument("--input", type=str, default="/dev/video0",
                        help="video source. If empty, uses webcam 0 stream")
    parser.add_argument("--out_filename", type=str, default="",
                        help="inference video name. Not saved if empty")
    parser.add_argument("--weights", default="./yolov4-tiny.weights",
                        help="yolo weights path")
    parser.add_argument("--dont_show", action='store_true',
                        help="windown inference display. For headless systems")
    parser.add_argument("--ext_output", action='store_true',
                        help="display bbox coordinates of detected objects")
    parser.add_argument("--config_file", default="./cfg/yolov4-tiny.cfg",
                        help="path to config file")
    parser.add_argument("--data_file", default="./cfg/coco.data",
                        help="path to data file")
    parser.add_argument("--thresh", type=float, default=.25,
                        help="remove detections with confidence below this value")
    return parser.parse_args()


def str2int(video_path):
    """
    argparse returns and string althout webcam uses int (0, 1 ...)
    Cast to int if needed
    """
    try:
        return int(video_path)
    except ValueError:
        return video_path


def check_arguments_errors(args):
    assert 0 < args.thresh < 1, "Threshold should be a float between zero and one (non-inclusive)"
    if not os.path.exists(args.config_file):
        raise(ValueError("Invalid config path {}".format(
            os.path.abspath(args.config_file))))
    if not os.path.exists(args.weights):
        raise(ValueError("Invalid weight path {}".format(
            os.path.abspath(args.weights))))
    if not os.path.exists(args.data_file):
        raise(ValueError("Invalid data file path {}".format(
            os.path.abspath(args.data_file))))
    if str2int(args.input) == str and not os.path.exists(args.input):
        raise(ValueError("Invalid video path {}".format(os.path.abspath(args.input))))


def set_saved_video(input_video, output_video, size):
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    # fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    fps = int(input_video.get(cv2.CAP_PROP_FPS))
    video = cv2.VideoWriter(output_video, fourcc, fps, size)
    return video


def image_detection(image, network, class_names, class_colors, thresh, width, height):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                               interpolation=cv2.INTER_LINEAR)

    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
    detections = darknet.detect_image(
        network, class_names, darknet_image, thresh=thresh)
    image = darknet.draw_boxes(detections, image_resized, class_colors)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), detections


DETECT_THREASHOLD = 0.5
NO_PERSON_CNT_THREASHOLD = 10


def isPerson(detections):
    personCnt = 0
    for label, confidence, bbox in detections:
        if label == "person":
            if float(confidence) > DETECT_THREASHOLD:
                personCnt += 1
                print("isPerson(): " + label + ", " + str(confidence))
    return personCnt


def video_cap():
    random.seed(3)  # deterministic bbox colors
    video = set_saved_video(cap, args.out_filename, (width, height))
    capflag = True
    start_time = time.time()

    bIllumination = False
    remo = NatureRemoController('Remo', myToken.default)
    noPersonCnt = 0

    while capflag:
        # print("Start")
        end_time = time.time()
        fps = 1/(end_time - start_time)
        start_time = end_time
        print("FPS: {}".format(fps))

        ret, frame = cap.read()
        if not ret:
            break

        print("width = " + str(width) + ", height = " + str(height))
        image, detections = image_detection(
            frame, network, class_names, class_colors, args.thresh, width, height
        )

        #darknet.print_detections(detections, args.ext_output)

        if isPerson(detections) > 0:
            noPersonCnt = 0
            if not bIllumination:
                bIllumination = True
                remo.sendOnSignalAilab('ailabキッチン照明')
                print("illumination on!")
        else:
            if bIllumination:
                noPersonCnt += 1
                print("noPersonCnt = " + str(noPersonCnt))
                if noPersonCnt >= NO_PERSON_CNT_THREASHOLD:
                    noPersonCnt = 0
                    bIllumination = False
                    remo.sendOffSignalAilab('ailabキッチン照明')
                    print("illumination off!")

        try:
            # if frame_resized is not None:
            if image is not None:
                print("video.write")
                video.write(image)
                print("cv2.imshow")
                cv2.imshow('Inference', image)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("push q")
                    capflag = False
                    break

        except:
            print("except break")
            capflag = False
            break

    cap.release()
    video.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    args = parser()
    check_arguments_errors(args)
    network, class_names, class_colors = darknet.load_network(
        args.config_file,
        args.data_file,
        args.weights,
        batch_size=1
    )
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    darknet_image = darknet.make_image(width, height, 3)
    input_path = str2int(args.input)
    cap = cv2.VideoCapture(input_path)

    print("video_cap start")
    video_cap()

    cap.release()
    cv2.destroyAllWindows()
