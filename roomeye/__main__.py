"""RoomEyeメイン

RoomEyeのメイン

"""
import traceback
from logging import Logger

import uvicorn

import roomeye.common.logging_manager as logging_manager
from roomeye.common.config_manager import ConfigManager
from roomeye.illmicontroller.illumination_controller import IlluminationController
from roomeye.webserver.webserver import WebServer

# ロガー
logger: Logger = logging_manager.get_logger()


class RoomEye():
    """RoomEyeメインクラス"""

    def __init__(self) -> None:
        self._config = ConfigManager().config
        self._illumi_controller = IlluminationController()
        self._web_server = WebServer(self._illumi_controller.notice_passing_sensor)

    def main(self) -> None:
        """メイン処理"""
        try:
            uvicorn.run(
                "roomeye.__main__:room_eye._web_server.app",
                host=self._config["web_server"]["host"],
                port=int(self._config["web_server"]["port"]),
                # reload=True,
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(
                {"action": "main", "ex": ex, "traceback": traceback.format_exc()}
            )
        logger.info({"action": "main", "msg": "finish"})


room_eye = RoomEye()
room_eye.main()
