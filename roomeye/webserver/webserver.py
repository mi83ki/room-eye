"""WEBサーバー通信部

WebAPIを提供する

"""

from logging import Logger
from typing import Callable

from fastapi import FastAPI, File, HTTPException, Response, UploadFile, status
from starlette.middleware.cors import CORSMiddleware

from roomeye.common import datadict, logging_manager
from roomeye.common.singleton import Singleton

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
        self.app = FastAPI()
        # APIのURL設定
        self.app.post("/api/v0/sensors")(self.post_sensors)

    # @app.post("/api/v0/sensors")
    async def post_sensors(self, body: datadict.SensorInfo) -> Response:
        """センサ情報登録要求
        curl -i -X POST -H "accept: application/json" -H "Content-Type: application/json" -d "{\"deviceId\":\"sensor15\", \"temperature\":\"25.4\", \"humidity\":\"55.4\", \"co2\":\"553.2\", \"passing\": true}" http://127.0.0.1:8000/api/v0/sensors

        Returns:
            dict: ロボット業務開始応答
        """
        logger.info({"action": "post_sensors", "body": body})
        if body.passing is not None:
            self._notice_passing_sensor(body.passing)
        return Response(status_code=200)
