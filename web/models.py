import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String, Boolean, UniqueConstraint, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from web.database import Base


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupsModel(BaseModel):
    __tablename__ = "groups"

    group_name = Column(String(50), unique=True, nullable=False)
    group_days = Column(Enum('Odd Days', 'Even Days', name='days_enum'), default='Odd Days', nullable=False)
    students = relationship(
        "StudentsModel",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class StudentsModel(BaseModel):
    __tablename__ = "students"

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True
    )

    group = relationship("GroupsModel", back_populates="students")
    results = relationship("StudentResultsModel", back_populates="student")


class WeeksModel(BaseModel):
    __tablename__ = "weeks"

    level = Column(Enum('Intermediate', 'Upper-Intermediate', 'IELTS', name='level_enum'), nullable=False)
    week_number = Column(Integer, unique=True, index=True, nullable=False)

    essential_from_unit = Column(Integer, index=True, nullable=False)
    essential_to_unit = Column(Integer, index=True, nullable=False)

    murphy_from_unit = Column(Integer, index=True, nullable=False)
    murphy_to_unit = Column(Integer, index=True, nullable=False)

    keys = Column(Integer, default=10, nullable=False)


class EssentialUnitsModel(BaseModel):
    __tablename__ = 'essential_units'

    level = Column(Enum('Intermediate', 'Upper-Intermediate', 'IELTS', name='level_enum'), nullable=False)
    unit_number = Column(Integer, nullable=False)
    words = relationship('EssentialWordsModel', back_populates='unit', cascade='all, delete-orphan')


class EssentialWordsModel(BaseModel):
    __tablename__ = 'essential_words'

    word = Column(String(50), nullable=False)
    meaning = Column(Text, nullable=False)

    translation_uz = Column(Text, nullable=False)
    translation_ru = Column(Text, nullable=False)

    unit_id = Column(UUID(as_uuid=True), ForeignKey('essential_units.id'), nullable=False)
    unit = relationship('EssentialUnitsModel', back_populates='words')
    results = relationship('StudentResultsModel', back_populates='vocabulary')


class MurphyUnitsModel(BaseModel):
    __tablename__ = 'murphy_units'

    level = Column(Enum('Intermediate', 'Upper-Intermediate', 'IELTS', name='level_enum'), nullable=False)
    unit_number = Column(Integer, nullable=False)
    exercises = relationship('MurphyExercisesModel', back_populates='unit', cascade='all, delete-orphan')


class MurphyExercisesModel(BaseModel):
    __tablename__ = "murphy_exercises"

    unit_id = Column(UUID(as_uuid=True), ForeignKey("murphy_units.id"), nullable=False)
    exercise_type = Column(String(50), nullable=False)
    instruction = Column(Text, nullable=False)

    unit = relationship('MurphyUnitsModel', back_populates='exercises')
    questions = relationship('MurphyExerciseQuestionsModel', back_populates='exercise', cascade='all, delete-orphan')
    results = relationship('StudentResultsModel', back_populates='exercise')


class MurphyExerciseQuestionsModel(BaseModel):
    __tablename__ = "murphy_exercise_questions"

    exercise_id = Column(UUID(as_uuid=True), ForeignKey("murphy_exercises.id"), nullable=False)
    blocks = Column(JSONB, nullable=False)
    correct_answer = Column(Text, nullable=False)

    exercise = relationship('MurphyExercisesModel', back_populates='questions')
    results = relationship('StudentResultsModel', back_populates='exercise_question')


class StudentResultsModel(BaseModel):
    __tablename__ = 'student_results'

    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    week_id = Column(UUID(as_uuid=True), ForeignKey('weeks.id'), nullable=False)
    type = Column(Enum('Exercise', 'Vocab', name='type_enum'), nullable=False)

    fails_count = Column(Integer, default=0)
    passed = Column(Boolean, default=False)

    exercise_id = Column(UUID(as_uuid=True), ForeignKey('murphy_exercises.id'), nullable=True)
    exercise_question_id = Column(UUID(as_uuid=True), ForeignKey('murphy_exercise_questions.id'), nullable=True)
    vocabulary_id = Column(UUID(as_uuid=True), ForeignKey('essential_words.id'), nullable=True)

    student = relationship('StudentsModel', back_populates='results')
    week = relationship('WeeksModel')
    vocabulary = relationship('EssentialWordsModel', back_populates='results')
    exercise = relationship('MurphyExercisesModel', back_populates='results')
    exercise_question = relationship('MurphyExerciseQuestionsModel', back_populates='results')