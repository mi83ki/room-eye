import time

# APIモジュールのインポート
from remo import NatureRemoAPI
import myToken


class NatureRemoController:
    """
    NatureRemoコントローラ
    """

    def __init__(self, deviceName):
        """
        コンストラクタ
        """
        # デバイス名
        self.deviceName = deviceName
        # 温度
        self.temperature = 0
        # 湿度
        self.humidity = 0
        # 照度
        self.illumination = 0
        # 人感センサ
        self.movement = 0

        # token指定
        self.api = NatureRemoAPI(myToken.default)
        # デバイス問い合わせ
        self.devices = self.api.get_devices()
        #print(self.devices)
        # 家電問い合わせ
        self.appliances = self.api.get_appliances()
        #print(self.appliances)

    def readDevice(self):
        """
        デバイス情報を取得する
        """
        self.devices = self.api.get_devices()
        for device in self.devices:
            if device.name == self.deviceName:
                self.temperature = device.newest_events["te"].val
                self.humidity = device.newest_events["hu"].val
                self.illumination = device.newest_events["il"].val
                self.movement = device.newest_events["mo"].val
                print(
                    str(self.temperature)
                    + ", "
                    + str(self.humidity)
                    + ", "
                    + str(self.illumination)
                    + ", "
                    + str(self.movement)
                )

    def sendOnSignalAilab(self, nickname):
        """
        オン信号を送信する

        Args:
            nickname (string): 家電名
        """
        for appliance in self.appliances:
            if appliance.nickname == nickname:
                for signal in appliance.signals:
                    if signal.name == "オン":
                        self.api.send_signal(appliance.signals[0].id)
                        print("### send on signal to " +
                              appliance.nickname + " ###")

    def sendOffSignalAilab(self, nickname):
        """
        照明を消す

        Args:
            nickname (string): 家電名
        """
        self.sendOnSignalAilab(nickname)
        time.sleep(1)
        self.sendOnSignalAilab(nickname)
        #time.sleep(1)
        #self.sendOnSignalAilab(nickname)
        #time.sleep(1)

    def sendOnSignal(self, nickname):
        """
        照明をつける

        Args:
            nickname (string): 家電名
        """
        for appliance in self.appliances:
            if appliance.nickname == nickname:
                self.api.send_light_infrared_signal(appliance.id, "on")
                print("### send on signal to " + appliance.nickname + " ###")

    def sendOffSignal(self, nickname):
        """
        照明を消す

        Args:
            nickname (string): 家電名
        """
        for appliance in self.appliances:
            if appliance.nickname == nickname:
                self.api.send_light_infrared_signal(appliance.id, "off")
                print("### send off signal to " + appliance.nickname + " ###")


if __name__ == "__main__":
    nrc = NatureRemoController("リビングRemo")
    while 1:
        nrc.readDevice()
        time.sleep(15)
