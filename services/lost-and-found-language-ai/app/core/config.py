
import os


class Settings:
    APP_NAME = "Lost and Found Language AI Service"

    APP_VERSION = "0.1.0"

    # 語言模型名稱
    MODEL_NAME = os.getenv(
        "MODEL_NAME",
        "Qwen/Qwen2.5-VL-3B-Instruct",
    )

    # 模型執行裝置
    DEVICE = os.getenv(
        "DEVICE",
        "auto",
    )

    # 是否啟用 4-bit 量化
    LOAD_IN_4BIT = os.getenv(
        "LOAD_IN_4BIT",
        "true",
    ).lower() == "true"

    # 模型生成文字的最大長度
    MAX_NEW_TOKENS = int(
        os.getenv(
            "MAX_NEW_TOKENS",
            "512",
        )
    )


settings = Settings()
