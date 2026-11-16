from app.services.embedding_service import EmbeddingService


embedding_service = EmbeddingService()


def load_models():
    """啟動時載入 AI 模型"""
    return embedding_service.load_model()
