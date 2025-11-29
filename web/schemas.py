from pydantic import BaseModel

class LoginRequest(BaseModel):
    login: str
    password: str

class GroupDaysRequest(BaseModel):
    days: int
    group: str
