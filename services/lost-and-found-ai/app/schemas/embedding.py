from pydantic import BaseModel, Field


class EmbeddingResponse(BaseModel):
    status: str = "success"
    filename: str
    model: str
    model_version: str
    embedding_dimension: int
    embedding: list[float] = Field(
        description="圖片的特徵向量"
    )
