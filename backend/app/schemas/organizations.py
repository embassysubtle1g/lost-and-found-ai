from pydantic import BaseModel, ConfigDict, Field


class OrganizationData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=240)
    phone: str = Field(min_length=1, max_length=50)
