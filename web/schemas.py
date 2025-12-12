from datetime import datetime

from pydantic import BaseModel, Field, validator

class LoginRequest(BaseModel):
    login: str
    password: str

class GroupDaysRequest(BaseModel):
    days: int
    group: str

class GroupTypeRequest(BaseModel):
    days: str

class AddWeekSchema(BaseModel):
    week_number: int
    level: str
    week_topic: str
    keys: int

    essential_from_unit: int
    essential_to_unit: int

    murphy_from_unit: int
    murphy_to_unit: int

class AddQuestionSchema(BaseModel):
    pass
