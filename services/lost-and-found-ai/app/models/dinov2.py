import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

from app.core.config import settings


class DinoV2Model:

    MODEL_MAPPING = {
        "dinov2_vits14": "facebook/dinov2-small",
        "dinov2_vitb14": "facebook/dinov2-base",
        "dinov2_vitl14": "facebook/dinov2-large",
        "dinov2_vitg14": "facebook/dinov2-giant",
    }

    def __init__(self):
        self.model_name = settings.MODEL_VERSION
        self.device = (
            "cuda"
            if settings.DEVICE == "auto" and torch.cuda.is_available()
            else "cpu"
            if settings.DEVICE == "auto"
            else settings.DEVICE
        )

        if self.model_name not in self.MODEL_MAPPING:
            raise ValueError(
                f"Unsupported model: {self.model_name}"
            )

        self.model_id = self.MODEL_MAPPING[self.model_name]

        self.processor = None
        self.model = None
        self.embedding_dimension = None

    def load(self):
        """載入 DINOv2 模型"""

        if self.device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(
                "DINOv2 requires CUDA, but no GPU is available. Check Docker Desktop GPU access and NVIDIA driver."
            )
        self.processor = AutoImageProcessor.from_pretrained(
            self.model_id
        )

        self.model = AutoModel.from_pretrained(
            self.model_id
        )

        self.model.to(self.device)
        self.model.eval()

        self.embedding_dimension = self.model.config.hidden_size

        return {
            "model": self.model_name,
            "model_id": self.model_id,
            "device": str(next(self.model.parameters()).device),
            "gpu_name": torch.cuda.get_device_name() if self.device.startswith("cuda") else None,
            "torch_version": str(torch.__version__),
            "cuda_version": torch.version.cuda,
            "embedding_dimension": self.embedding_dimension,
            "status": "loaded",
        }

    def extract_embedding(self, image: Image.Image):
        """將圖片轉換成正規化特徵向量"""

        if self.model is None:
            raise RuntimeError("Model has not been loaded")

        inputs = self.processor(
            images=image.convert("RGB"),
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            outputs = self.model(**inputs)

        # 使用整張圖片的 CLS Token 作為特徵
        embedding = outputs.last_hidden_state[:, 0, :]

        # 正規化，方便後續計算餘弦相似度
        embedding = torch.nn.functional.normalize(
            embedding,
            p=2,
            dim=1,
        )

        return embedding.cpu().numpy()[0]