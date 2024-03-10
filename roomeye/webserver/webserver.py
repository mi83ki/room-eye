"""WEBサーバー通信部

WebAPIを提供する

"""

from logging import Logger
from typing import Callable

from fastapi import FastAPI, Response

from roomeye.common import logging_manager
from roomeye.common.singleton import Singleton

from .api.models import SensorInfo

# ロガー
logger: Logger = logging_manager.get_logger()


class WebServer(metaclass=Singleton):
    """WEBサーバー通信クラス"""

    def __init__(
        self,
        notice_passing_sensor: Callable[[bool], None],
    ) -> None:
        # コールバック関数
        self._notice_passing_sensor: Callable[[bool], None] = notice_passing_sensor
        # FastAPI
        self._app = FastAPI(
            title="room-eye Web API",
            version="0.0.0",
        )
        # APIのURL設定
        self._app.post("/api/v0/sensors", response_model=None)(self.post_sensors)

    @property
    def app(self) -> FastAPI:
        """FastAPIのappを取得する

        Returns:
            FastAPI: _description_
        """
        return self._app

    # @app.post("/api/v0/sensors")
    async def post_sensors(self, body: SensorInfo) -> Response:
        """センサ情報登録要求
        curl -i -X POST -H "accept: application/json" -H "Content-Type: application/json" -d "{\"deviceId\":\"sensor15\", \"temperature\":\"25.4\", \"humidity\":\"55.4\", \"co2\":\"553.2\", \"passing\": true}" http://127.0.0.1:8000/api/v0/sensors
        """
        logger.info({"action": "post_sensors", "body": body})
        if body.passing is not None:
            self._notice_passing_sensor(body.passing)
        return Response(status_code=200)
