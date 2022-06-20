# human-detector

人を検知して家電を操作するアプリ

## 概要

部屋に定点カメラを設置して以下を実現する

- 人の入室を検知して照明をONにする
- 人の退室を検知して照明をOFFにする
- 人がベッドで横になったことを検知して照明をOFFにする
- 人がベッドから起き上がったことを検知して照明をONにする

## 使用したもの

1. Jetson Nano 2GB
1. USBカメラ

## インストール手順

1. サブモジュールをチェックアウトする

    ```bash
    git submodule update --init
    ```

## やったこと

### Jetson NanoでYolo V4を使用する

- 参考にしたページ：<https://zenn.dev/rain_squallman/articles/eec4916653d1bdcb2550>
- 参考にしたページ：<https://denor.jp/jetson-nano%E3%81%A7yolov4%E3%82%92%E5%8B%95%E3%81%8B%E3%81%97%E3%81%A6%E3%81%BF%E3%81%BE%E3%81%97%E3%81%9F>

```bash
git clone https://github.com/AlexeyAB/darknet
cd darknet
vim Makefile
```

Makefileの中身を以下のように変更する。
LIBSO=1とすることで、pythonからdarknetを利用できるようになる。

```txt
GPU=1
CUDNN=1
CUDNN_HALF=1
OPENCV=1
LIBSO=1
# 77行目付近
NVCC=/usr/local/cuda/bin/nvcc
```

makeする

```bash
make
```

Yolo v4のweightファイルを取得する

```bash
wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights
```

camberra-gtk-moduleが入ってないとfailed to load module errorが出るらしいのでインストール

```bash
sudo apt-get install libcanberra-gtk-module -y
```

お試し実行

```bash
./darknet detect yolov4-tiny.cfg yolov4-tiny.weights data/dog.jpg
```

このコマンドだと途中でクラッシュするのでyolov4-tinyだといけた

```bash
wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights
cd cfg/
./darknet detect cfg/yolov4-tiny.cfg yolov4-tiny.weights data/dog.jpg
```

カメラ入力からリアルタイムで画像処理

```bash
./darknet detector demo cfg/coco.data cfg/yolov4-tiny.cfg yolov4-tiny.weights /dev/video0
```

### USBカメラの認識

v4l2をインストールしてみた→/dev/video0がない

```bash
sudo apt install v4l-utils 
```

USBカメラを認識しない件の対策→解決しない
<https://kinacon.hatenablog.com/entry/2018/08/10/012030>

```bash
sudo mknod /dev/video0 c 81 0
sudo chmod 666 /dev/video0
sudo chown root.video /dev/video0
modprobe -a uvcvideo
```

このページが参考になった
<https://tarufu.info/ubuntu-ucam-dle300t/>

```bash
dmesg | grep -i usb
```

このコマンドで調べると、USBカメラをそもそも認識していないことがわかった。
USBカメラを抜き差しすると、解決。

### pythonコードでdarknetを利用する

1. 必要なライブラリをインストールする

    ```bash
    sudo apt install python3-pip
    ```

1. デモプログラムを実行する

    ```bash
    python3 darknet_video.py --input /dev/video0 --weights yolov4-tiny.weights --config_file cfg/yolov4-tiny.cfg
    ```

    →なぜかOpenCVのエラーが出る

    ```bash
    [ERROR:1] global /home/nvidia/host/build_opencv/nv_opencv/modules/videoio/src/cap.cpp (392) open VIDEOIO(GSTREAMER): raised OpenCV exception:

    OpenCV(4.1.1) /home/nvidia/host/build_opencv/nv_opencv/modules/videoio/src/cap_gstreamer.cpp:1391: error: (-215:Assertion failed) !filename.empty() in function 'open'

    [ERROR:1] global /home/nvidia/host/build_opencv/nv_opencv/modules/videoio/src/cap.cpp (392) open VIDEOIO(CV_IMAGES): raised OpenCV exception:

    OpenCV(4.1.1) /home/nvidia/host/build_opencv/nv_opencv/modules/videoio/src/cap_images.cpp:207: error: (-215:Assertion failed) !filename.empty() in function 'icvExtractPattern'
    ```

1. こちらで紹介されているのサンプルコードに変更すると起動できた！
    <http://kazuki-room.com/how_to_detect_objects_by_putting_darknet_alexeyab_in_jetson_nano/>
    「darknet_video2.py」

    ```python
    import argparse
    import os
    import glob
    import random
    import darknet
    import time
    import cv2
    import numpy as np
    import darknet
    
    def parser():
        parser = argparse.ArgumentParser(description="YOLO Object Detection")
        parser.add_argument("--input", type=str, default=0,
                            help="video source. If empty, uses webcam 0 stream")
        parser.add_argument("--out_filename", type=str, default="",
                            help="inference video name. Not saved if empty")
        parser.add_argument("--weights", default="yolov4.weights",
                            help="yolo weights path")
        parser.add_argument("--dont_show", action='store_true',
                            help="windown inference display. For headless systems")
        parser.add_argument("--ext_output", action='store_true',
                            help="display bbox coordinates of detected objects")
        parser.add_argument("--config_file", default="./cfg/yolov4.cfg",
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
            raise(ValueError("Invalid config path {}".format(os.path.abspath(args.config_file))))
        if not os.path.exists(args.weights):
            raise(ValueError("Invalid weight path {}".format(os.path.abspath(args.weights))))
        if not os.path.exists(args.data_file):
            raise(ValueError("Invalid data file path {}".format(os.path.abspath(args.data_file))))
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
        detections = darknet.detect_image(network, class_names, darknet_image, thresh=thresh)
        image = darknet.draw_boxes(detections, image_resized, class_colors)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), detections
    
    
    def video_cap():
        random.seed(3)  # deterministic bbox colors
        video = set_saved_video(cap, args.out_filename, (width, height))
        capflag = True
        start_time = time.time()
        while capflag:
            #print("Start")
            end_time = time.time()
            fps = 1/(end_time - start_time)
            start_time = end_time
            print("FPS: {}".format(fps))
    
            ret, frame = cap.read()
            if not ret:
                break
    
            image, detections = image_detection(
              frame, network, class_names, class_colors, args.thresh, width, height
              )
    
            darknet.print_detections(detections, args.ext_output)
    
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
    ```

    起動コマンド

    ```bash
    python3 darknet_video2.py --input /dev/video0 --weights yolov4-tiny.weights --config_file cfg/yolov4-tiny.cfg
    ```

### 人を検知したら照明を操作する

- image_detection()の戻り値であるdetectionsに検出結果が格納されている
- detectionのメンバーは以下
  - label：ラベル（"person"とか）
  - confidence：認識精度[％]
  - bbox：バウンディングボックスの位置とサイズ
- 一定の認識精度以上の"person"が検知した場合に人がいると判定して照明をONするコードを追加する

    ```python
    def isPerson(detections):
        personCnt = 0
        for label, confidence, bbox in detections:
            if label == "person":
                if float(confidence) > DETECT_THREASHOLD:
                    personCnt += 1
                    print("isPerson(): " + label + ", " + str(confidence))
        return personCnt

    def video_cap():
        ・・・
        bIllumination = False
        remo = NatureRemoController('Remo')
        noPersonCnt = 0

        while capflag:
            ・・・
            if isPerson(detections) > 0:
                if not bIllumination:
                    bIllumination = True
                    remo.sendOnSignalAilab('ailab繧ｭ繝・メ繝ｳ辣ｧ譏・)
                    print("illumination on!")
            else:
                if bIllumination:
                    noPersonCnt += 1
                    print("noPersonCnt = " + str(noPersonCnt))
                    if noPersonCnt >= NO_PERSON_CNT_THREASHOLD:
                        noPersonCnt = 0
                        bIllumination = False
                        remo.sendOffSignalAilab('ailab繧ｭ繝・メ繝ｳ辣ｧ譏・)
                        print("illumination off!")
            ・・・

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
    ```

### VMware Ubuntu 20.04 でmediapipeを利用

参考にしたURL：<https://nullpo24.hatenablog.com/entry/2021/05/15/215427>

1. mediapipeをインストールする

    ```bash
    pip install mediapipe
    ```

2. protobufを3.20.X以下にしないとmediapipeをインポートできなかったため、ダウングレードする

    ```bash
    pip install protobuf==3.20.1
    ```

3. USBカメラの認識確認
    - 以下のコマンドで「/dev/video0」があればOK

        ```bash
        ls /dev/video*
        ```

    - 以下のコマンドでカメラ画像をチェックする

        ```bash
        cheese
        ```

    - VMwareでUbuntu20.04の環境を構築している場合にUSBカメラがうまく認識できなかったが、仮想マシン設定→USBコントローラ→USBの互換性を「USB 3.1」に変更して再起動することで認識できた。

4. サンプルコードを実行する
    - [Kazuhito00](https://github.com/Kazuhito00/mediapipe-python-sample)さんのサンプルコードを利用させていただいた。

        ```bash
        git clone https://github.com/Kazuhito00/mediapipe-python-sample
        cd mediapipe-python-sample
        python3 sample_pose.py
        ```

### Jetson Nanoでmediapipeを動かす

参考にしたサイト
<https://dev.classmethod.jp/articles/mediapipe-install-on-jetson-nano-with-cpu-gpu/>

1. 前準備

    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo reboot
    ```

2. MediaPipeをインストール

    ```bash
    cd ~
    git clone https://github.com/google/mediapipe.git
    cd ~/mediapipe
    chmod +x setup_opencv.sh
    ```

3. Bazelインストール

    ```bash
    sudo apt install build-essential openjdk-8-jdk python zip unzip
    sudo apt install apt-transport-https curl gnupg

    git clone https://github.com/PINTO0309/Bazel_bin.git
    cd Bazel_bin/3.7.2/aarch64
    cd Bazel_bin/2.0.0/Ubuntu1804_JetsonNano_aarch64/openjdk-8-jdk/
    ./install.sh

    mkdir bazel
    cd bazel
    wget https://github.com/bazelbuild/bazel/releases/download/3.7.2/bazel-3.7.2-dist.zip
    unzip bazel-3.7.2-dist.zip
    env EXTRA_BAZEL_ARGS="--host_javabase=@local_jdk//:jdk" bash ./compile.sh
    ```

これではうまく行かなかった。

次に参考にしたサイト

- YouTube動画：<https://www.youtube.com/watch?v=ij9bIET4rCU>
- テキストファイル：<https://github.com/feitgemel/Jetson-Nano-Python/blob/master/Install-MediaPipe/How%20to%20Install%20MediaPipe%20on%20jetson-nano%202022.txt>

1. Swapがない場合は追加する

    ```bash
    ```

2. 各種パッケージのインストール

    ```bash
    pip sinstall
    sudo apt install python3-pip
    sudo pip3 install -U pip testresources setuptools==49.6.0
    sudo apt install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran
    sudo pip3 install -U --no-deps numpy==1.19.4 future==0.18.2 mock==3.0.5 keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 protobuf pybind11 cython pkgconfig
    sudo env H5PY_SETUP_REQUIRES=0 pip3 install -U h5py==3.1.0
    sudo apt-get install python3-opencv
    ```

3. opencvのセットアップ

    ```bash
    git clone https://github.com/google/mediapipe.git
    cd mediapipe
    sudo apt-get install -y libopencv-core-dev  libopencv-highgui-dev libopencv-calib3d-dev libopencv-features2d-dev libopencv-imgproc-dev libopencv-video-dev
    sudo chmod 744 setup_opencv.sh
    ./setup_opencv.sh
    ```

    JetsonNano 2GBでは3時間程度かかりました。

4. mediapipeのインストール

    ```bash
    sudo pip3 install opencv_contrib_python
    git clone https://github.com/PINTO0309/mediapipe-bin
    cd mediapipe-bin

    sudo apt install curl

    sudo chmod +x ./v0.8.5/download.sh && ./v0.8.5/download.sh
    unzip v0.8.5.zip
    cd v0.8.5/numpy119x/py36/
    sudo pip3 install ./mediapipe-0.8.5_cuda102-cp36-cp36m-linux_aarch64.whl

    pip3 install dataclasses
    ```

    上記手順だとnumpyがインストールできなかったので以下のURLからダウンロード
    <https://drive.google.com/file/d/1lHr9Krznst1ugLF_ElWGCNi_Y4AmEexx/view?usp=sharing>

    - 参考にしたサイト：<https://github.com/Melvinsajith/How-to-Install-Mediapipe-in-Jetson-Nano>

    ```bash
    mv ~/Downloads/mediapipe-bin.zip ~/mediapipe
    cd mediapipe
    unzip mediapipe-bin.zip
    cd mediapipe
    sudo pip3 install numpy-1.19.4-cp36-none-manylinux2014_aarch64.whl
    ```

5. デモの実行

    ```bash
    git clone https://github.com/feitgemel/BodyPos.git
    cd BodyPos
    cd MediaPipe
    cd Demo
    python3 MediaPipe-Holistic.py
    ```

### 寝ころび検知

mediapipeを用いて寝ころび検知を行う。

#### ランドマーク

mediapipeで検出したランドマークを活用する。
今回はresults.pose_landmarksを利用する。

姿勢のランドマークは以下のインデックスで取得できる。
画像取得元URL：<https://google.github.io/mediapipe/solutions/pose.html>

![pose_landmarks](image/pose_tracking_full_body_landmarks.png)

#### 寝ころび検知アルゴリズム

右肩と右腰を繋いだ線が45°よりも水平　かつ　左肩と左腰を繋いだ線が45°よりも水平
の場合に寝ころびと判定する

#### サンプルプログラム

```python
def isLieDown(pose_landmarks):
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
        if xdefR > ydefR:
            lieDownR = True

    if landmarkLeftShoulder != None and landmarkLeftHip != None:
        xdefL = abs(landmarkLeftShoulder.x - landmarkLeftHip.x)
        ydefL = abs(landmarkLeftShoulder.y - landmarkLeftHip.y)
        if xdefL > ydefL:
            lieDownL = True
    return lieDownR and lieDownL
```
