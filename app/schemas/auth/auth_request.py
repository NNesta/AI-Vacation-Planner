from pydantic import BaseModel, EmailStr, Field


class RegisterUser(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=150)
    username: str = Field(min_length=1, max_length=50)
