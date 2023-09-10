"""照明制御部

通過検知情報や人検知情報を元に照明を制御する

"""

import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from libs.natureremocon.natureremocon.natureremocon import NatureRemoController


class IlluminationController:
    """照明制御クラス"""

    def __init__(self) -> None:
        # 環境変数を読み込む
        load_dotenv()
        NATURE_REMO_TOKEN = os.environ.get(
            "NATURE_REMO_TOKEN", "Your Nature Remo Token"
        )
        self._ROOM_LIGHT_NAME = os.environ.get("ROOM_LIGHT_NAME", "Your Light Name")
        self._remo = NatureRemoController(NATURE_REMO_TOKEN)

    def light_on(self) -> bool:
        return self._remo.send_on_signal_light(self._ROOM_LIGHT_NAME)

    def light_off(self) -> bool:
        return self._remo.send_off_signal_light(self._ROOM_LIGHT_NAME)

    def notice_passing_sensor(self, passing: bool) -> None:
        if passing:
            self.light_on()
