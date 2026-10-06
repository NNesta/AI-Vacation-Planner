from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginResponse(BaseModel):

    access_token: str
    token_type: str


class RegisterUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)
