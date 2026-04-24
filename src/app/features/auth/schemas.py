from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterUser(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=150)


class RegisterUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)


class LoginResponse(BaseModel):
    # model_config = ConfigDict(from_attributes=True)

    token: str
    token_type: str = "jwt"
