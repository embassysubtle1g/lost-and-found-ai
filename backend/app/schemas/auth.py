from pydantic import BaseModel, Field


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=160)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=160)
    new_password: str = Field(min_length=10, max_length=160)


class Organization(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=240)
    phone: str = Field(min_length=1, max_length=50)
