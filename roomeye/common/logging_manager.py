"""ロガー管理部

ロギングインスタンスの生成を行う

"""

import logging.config
import os


def get_logger(name: str = "root") -> logging.Logger:
    """ロガーを取得する

    Args:
        name (str): ロガー名

    Returns:
        _type_: ロガー
    """
    # logsフォルダが無ければ作成する
    if os.path.isdir("./logs") is False:
        os.mkdir("./logs")
    # ロガー
    logging.config.fileConfig("config/logging.ini")
    return logging.getLogger(name)
