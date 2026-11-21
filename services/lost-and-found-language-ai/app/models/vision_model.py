from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings


class VisionModelManager:
    """延遲載入並管理圖片理解模型，避免服務啟動時立即下載模型。"""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._processor: Any | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._processor is not None

    def load(self) -> None:
        if self.is_loaded:
            return

        import torch
        from transformers import (
            AutoProcessor,
            BitsAndBytesConfig,
            Qwen2_5_VLForConditionalGeneration,
        )

        model_kwargs: dict[str, Any] = {
            "device_map": "auto" if settings.DEVICE == "auto" else settings.DEVICE,
        }

        if settings.LOAD_IN_4BIT:
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "目前環境沒有可用的 CUDA GPU，無法使用 4-bit 量化載入模型。"
                )

            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

        self._processor = AutoProcessor.from_pretrained(settings.MODEL_NAME)
        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            settings.MODEL_NAME,
            **model_kwargs,
        )
        self._model.eval()

    def generate(self, image: Any, prompt: str) -> str:
        if settings.MODEL_BACKEND == "ollama":
            from app.models.ollama_vision import generate
            return generate(image, prompt)
        self.load()

        import torch
        from qwen_vl_utils import process_vision_info

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        text = self._processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self._model.device)

        with torch.inference_mode():
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=settings.MAX_NEW_TOKENS,
                do_sample=False,
            )

        new_tokens = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
        ]
        return self._processor.batch_decode(
            new_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()


@lru_cache(maxsize=1)
def get_vision_model() -> VisionModelManager:
    return VisionModelManager()
