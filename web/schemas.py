from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator

class LoginRequest(BaseModel):
    login: str
    password: str

class GroupDaysRequest(BaseModel):
    days: int
    group: str
    level: str

class AddWordSchema(BaseModel):
    book_id: str
    unit_id: str
    meaning: str
    word: str
    translation_uz: str
    translation_ru: str
    word_photo: str

class GroupTypeRequest(BaseModel):
    days: str

class AddWeekSchema(BaseModel):
    week_number: int
    level: str
    week_topic: str
    keys: int

    essential_book: str
    essential_from_unit: int
    essential_to_unit: int

    murphy_book: str
    murphy_from_unit: int
    murphy_to_unit: int

class AddEssentialUnitSchema(BaseModel):
    book_id: str
    unit_number: int

class AddExerciseSchema(BaseModel):
    unit_id: str
    condition: str
    type: int
    exercise_number: int

class AddExerciseQuestionSchema(BaseModel):
    exercise_id: str
    field: dict

class ResultItem(BaseModel):
    question_id: str
    failed: bool

class SaveResultsSchema(BaseModel):
    exercise_id: str
    week_id: str
    results: List[ResultItem]
