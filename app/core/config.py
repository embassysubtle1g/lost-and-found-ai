import os


class Settings:
    APP_NAME = "Lost and Found AI Service"

    # 模型設定
    MODEL_NAME = os.getenv("MODEL_NAME", "dinov2")
    MODEL_VERSION = os.getenv(
        "MODEL_VERSION",
        "dinov2_vitb14",
    )

    # 特徵向量維度
    EMBEDDING_DIMENSION = int(
        os.getenv("EMBEDDING_DIMENSION", "768")
    )

    # 模型運算裝置
    DEVICE = os.getenv("DEVICE", "auto")


settings = Settings()