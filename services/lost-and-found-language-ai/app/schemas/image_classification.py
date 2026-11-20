from pydantic import BaseModel, Field


class ImageAttributes(BaseModel):
    color: str | None = None
    material: str | None = None
    brand: str | None = None
    distinctive_features: list[str] = Field(default_factory=list)


class ImageClassificationResponse(BaseModel):
    detected_item: str = Field(description="圖片中辨識出的具體物品名稱")
    suggested_category: str = Field(description="建議主系統採用的通用分類名稱")
    description: str = Field(description="物品外觀描述")
    attributes: ImageAttributes
    confidence: float = Field(ge=0, le=1, description="模型自評信心程度，僅供參考")
    needs_review: bool = Field(description="是否需要人工確認")
