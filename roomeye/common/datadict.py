"""データ辞書

各要求、応答のデータ辞書を定義する

"""

from pydantic import BaseModel, Field


class SensorInfo(BaseModel):
    """センサー情報"""

    deviceId: str = Field(examples=["sensor01"])
    temperature: float | None = None
    humidity: float | None = None
    co2: float | None = None
    illumination: float | None = None
    soilTemperature: float | None = None
    soilHumidity: float | None = None
    ec: float | None = None
    ph: float | None = None
    passing: bool | None = None
