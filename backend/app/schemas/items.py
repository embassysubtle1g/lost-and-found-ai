from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ItemData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    found_date: date
    found_location: str = Field(min_length=1, max_length=240)
    private_note: str = Field(default="", max_length=2000)
