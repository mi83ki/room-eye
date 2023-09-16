<!-- omit in toc -->
# RoomEye

人を検知して家電を操作するアプリ

<!-- omit in toc -->
## 目次

- [1. 概要](#1-概要)
- [2. 使用するもの](#2-使用するもの)
- [3. インストール手順](#3-インストール手順)
  - [3.1. Pythonのインストール](#31-pythonのインストール)
  - [3.2. 仮想環境の構築](#32-仮想環境の構築)
    - [3.2.1. Windowsの場合](#321-windowsの場合)
      - [3.2.1.1. エラー：「スクリプトの実行が無効」が発生する場合](#3211-エラースクリプトの実行が無効が発生する場合)
    - [3.2.2. Linuxの場合](#322-linuxの場合)
  - [3.3. Pythonライブラリのインストール](#33-pythonライブラリのインストール)
  - [3.4. サブモジュールをチェックアウトしてライブラリをインストール](#34-サブモジュールをチェックアウトしてライブラリをインストール)
  - [3.5. NatureRemoトークンを設定する](#35-natureremoトークンを設定する)
- [4. 起動](#4-起動)

## 1. 概要

部屋に定点カメラを設置して以下を実現する

- 人の入室を検知して照明をONにする
- 人の退室を検知して照明をOFFにする
- 人がベッドで横になったことを検知して照明をOFFにする
- 人がベッドから起き上がったことを検知して照明をONにする

## 2. 使用するもの

1. Jetson Nano 2GB
1. USBカメラ

## 3. インストール手順

### 3.1. Pythonのインストール

以下を参考にダウンロード・インストールする\
<https://www.javadrive.jp/python/install/index1.html>

- バージョンは3.10.11を推奨\
    <https://www.python.org/downloads/release/python-31011/>

### 3.2. 仮想環境の構築

以下のコマンドで仮想環境を構築する

~~~bash
python -m venv venv
~~~

以下のコマンドで仮想環境を有効にする

#### 3.2.1. Windowsの場合

~~~bash
.\venv\Scripts\Activate.ps1
~~~

##### 3.2.1.1. エラー：「スクリプトの実行が無効」が発生する場合

もし以下のエラーが発生した場合はPowerShellのスクリプト実行ポリシーを変更する必要がある。

~~~bash
.\venv\Scripts\Activate.ps1 : このシステムではスクリプトの実行が無効になっているため、
ファイル C:\Users\bumble-eye\Documents\bumble-eye\backend\venv\Scripts\Activate.ps1 を読み込むことができません。
~~~

1. PowerShellを管理者権限で開く
1. 以下のコマンドを実行する

    ~~~bash
    Get-ExecutionPolicy
    Set-ExecutionPolicy RemoteSigned
        Yを入力
    Get-ExecutionPolicy
    ~~~

1. VSCodeを再起動する

#### 3.2.2. Linuxの場合

~~~bash
source venv/bin/activate
~~~

### 3.3. Pythonライブラリのインストール

以下のコマンドを実行する

~~~bash
pip install -r requirements.txt
~~~

### 3.4. サブモジュールをチェックアウトしてライブラリをインストール

~~~bash
git submodule update --init
cd libs/natureremocon/
pip install -r requirements.txt
~~~

### 3.5. NatureRemoトークンを設定する

`roomeye/.env.example`を複製し、`roomeye/.env`にファイル名を変更する。\
ファイルを開いて必要な情報を更新する

## 4. 起動

以下のコマンドで起動する

~~~bash
# リポジトリのルートディレクトリroom-eye/に移動する
python -m room-eye 
~~~
