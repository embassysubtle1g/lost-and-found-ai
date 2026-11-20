from PIL import Image

from app.models.dinov2 import DinoV2Model


class EmbeddingService:
    """管理圖片特徵擷取服務"""

    def __init__(self):
        self.model_manager = DinoV2Model()
        self.model_info = None

    def load_model(self):
        """載入 DINOv2 模型"""
        self.model_info = self.model_manager.load()
        return self.model_info

    def extract_embedding(self, image: Image.Image):
        """將圖片轉換成特徵向量"""

        if self.model_info is None:
            raise RuntimeError("Embedding model has not been loaded")

        embedding = self.model_manager.extract_embedding(image)

        return embedding.tolist()

    def get_model_info(self):
        """取得目前模型資訊"""

        if self.model_info is None:
            return {
                "status": "not_loaded"
            }

        return self.model_info
