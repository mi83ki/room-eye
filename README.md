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

## やったこと

### Jetson NanoでYolo V4を使用する

- 参考にしたページ：<https://zenn.dev/rain_squallman/articles/eec4916653d1bdcb2550>
- 参考にしたページ：<https://denor.jp/jetson-nano%E3%81%A7yolov4%E3%82%92%E5%8B%95%E3%81%8B%E3%81%97%E3%81%A6%E3%81%BF%E3%81%BE%E3%81%97%E3%81%9F>

```bash
git clone https://github.com/AlexeyAB/darknet
cd darknet
vim Makefile
```

```txt
GPU=1
CUDNN=1
CUDNN_HALF=1
OPENCV=1
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
