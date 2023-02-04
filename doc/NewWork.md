# ReadMyFace

2022年度4Q自由研究テーマの開発内容

## イシュー

**音声入力（Alexaなど）が一般に普及すると、音声すら不要とする入力が求められる**\
家にいるときくらい、言葉にしなくても、俺のやりたいことを認識してくれ頼むから！

## 過去の取り組み

過去の取り組みを整理する

### 取り組み1：言葉にしなくても察してくれる拡張

書斎のPCにログインすると自動でリビングの照明を消し、書斎の照明をONしてくれる
![step1](img/step1.drawio.svg)

### 取り組み2：言葉にしなくても察してくれる拡張Ver.2

測距センサ×2で人の通過を検知して、照明をON/OFFしてくれる

### 取り組み3：RoomEye

存在だけでなく、寝ころびも検知してスマートに家電を操作
<https://www.youtube.com/watch?v=W6YuXV-dDOQ>

![step3](img/step3.drawio.svg)

### 取り組み4：HandX

- アレクサを日常的に使っているが、いちいち言葉にするのが面倒くさいと思うことがある。\
    ※「アレクサ、テレビのチャンネルを8chにして」とか言うの大変

- 今回は人差し指のスワイプで家電を操作できるアプリを開発。\
    （会社の研修でグループテーマとして開発）

- ROSロボを活用してユーザーの手を追従する仕組みも構築。\

<https://www.youtube.com/watch?v=W6YuXV-dDOQ>

![step4](img/step4.drawio.svg)

## 今回取り組むこと

### イシュー

**音声入力（Alexaなど）が一般に普及すると、音声すら不要とする入力が求められる**\
家にいるときくらい、言葉にしなくても、俺のやりたいことを認識してくれ頼むから！

### 具体内容

これまでの取り組みの集大成として、「察してくれる拡張」を完成させる。\
具体的には以下の機能を実装する。

- 通過検知センサによる通過検知で、部屋の照明をタイムリーに制御（カメラでの人検知ではワンテンポ遅れるが、通過センサは速い）
- カメラによる人検知で、消灯の判断（複数の人間が部屋に侵入した場合、通過センサのみの場合は総人数をカウントしないと誤って消灯してしまうが、カメラで人の存在を検知できれば人数カウントが不要）
- カメラによる姿勢検知で、寝るときに自動消灯

![step5](img/step5.drawio.svg)