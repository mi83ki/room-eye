"""RoomEyeメイン

RoomEyeのメイン

"""
import traceback
from logging import Logger

import uvicorn
from fastapi import FastAPI

import roomeye.common.logging_manager as logging_manager
from roomeye.common.config_manager import ConfigManager
from roomeye.illmicontroller.illumination_controller import IlluminationController
from roomeye.imgdetector.human_detector import HumanDetector
from roomeye.webserver.webserver import WebServer

# ロガー
logger: Logger = logging_manager.get_logger()
# 設定
config = ConfigManager().config


class RoomEye:
    """RoomEyeメインクラス"""

    def __init__(self) -> None:
        self._illumi_controller = IlluminationController()
        self._web_server = WebServer(self._illumi_controller.notice_passing_sensor)

        # self._human_detector = HumanDetector()

    @property
    def app(self) -> FastAPI:
        """FastAPIのappを取得する

        Returns:
            FastAPI: _description_
        """
        return self._web_server.app


room_eye = RoomEye()
try:
    uvicorn.run(
        room_eye.app,
        host=config["web_server"]["host"],
        port=int(config["web_server"]["port"]),
    )
except Exception as ex:  # pylint: disable=broad-exception-caught
    logger.error({"action": "main", "ex": ex, "traceback": traceback.format_exc()})
logger.info({"action": "main", "msg": "finish"})
