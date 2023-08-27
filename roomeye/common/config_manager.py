"""コンフィグ管理部

コンフィグファイル(config/config.ini)を読み込んで設定情報をメモリに保持する

"""

import configparser

from . import logging_manager
from .singleton import Singleton


class ConfigManager(metaclass=Singleton):
    """設定値管理クラス"""

    def __init__(self) -> None:
        """コンストラクタ"""
        self._logger = logging_manager.get_logger()
        self._config = self.read_config("config/config.ini")

    def read_config(self, file_path: str) -> dict:
        """指定したコンフィグファイルを読み込む

        Args:
            file_path (str): コンフィグファイルのパス

        Returns:
            dict: 読み込んだ設定値
        """
        config = configparser.ConfigParser()
        config.read(file_path)
        # 辞書型に変換
        config_dict = {
            s: {i[0]: i[1] for i in config.items(s)} for s in config.sections()
        }
        self._logger.info({"action": "read_config", "config": config_dict})
        return config_dict

    @property
    def config(self) -> dict:
        """設定値を取得する

        Returns:
            dict: 設定値
        """
        return self._config
