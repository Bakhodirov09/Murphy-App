import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String, Boolean, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from web.general import tashkent
from web.database import Base


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    created_at = Column(DateTime, default=datetime.now(tashkent))
    updated_at = Column(DateTime, default=datetime.now(tashkent), onupdate=datetime.now(tashkent))

class GroupsModel(BaseModel):
    __tablename__ = "groups"

    group_name = Column(String(50), unique=True, nullable=False)
    group_days = Column(Enum('Odd Days', 'Even Days', name='days_enum'), nullable=False)
    group_level = Column(Enum('Upper-Intermediate', 'IELTS', name='level_enum'), nullable=False)

    students = relationship(
        "StudentsModel",
        back_populates="group",
        cascade="all, delete-orphan"
    )

class StudentsModel(BaseModel):
    __tablename__ = "students"

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    avatar_url = Column(String(500))
    chat_id = Column(BigInteger, unique=True)

    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True
    )

    group = relationship("GroupsModel", back_populates="students")
    results = relationship("StudentResultsModel", back_populates="student", cascade='all, delete-orphan')

class StudentResultsModel(BaseModel):
    __tablename__ = 'student_results'

    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    week_id = Column(UUID(as_uuid=True), ForeignKey('weeks.id', ondelete='CASCADE'), nullable=False)

    type = Column(Enum('Exercise', 'Vocab', name='type_enum'), nullable=False)
    fails_count = Column(Integer, default=0)
    passed = Column(Boolean, default=False)

    exercise_id = Column(UUID(as_uuid=True), ForeignKey('murphy_exercises.id', ondelete='CASCADE'))
    exercise_question_id = Column(UUID(as_uuid=True), ForeignKey('murphy_exercise_questions.id', ondelete='CASCADE'))
    vocabulary_unit_id = Column(UUID(as_uuid=True), ForeignKey('essential_units.id', ondelete='CASCADE'))
    vocabulary_id = Column(UUID(as_uuid=True), ForeignKey('essential_words.id', ondelete='CASCADE'))

    student = relationship("StudentsModel", back_populates="results")
    week = relationship("WeeksModel")

    vocabulary = relationship("EssentialWordsModel", back_populates="results")
    vocabulary_unit = relationship("EssentialUnitsModel", back_populates="results")

    exercise = relationship("MurphyExercisesModel", back_populates="results")
    exercise_question = relationship("MurphyExerciseQuestionsModel", back_populates="results")

class WeekScheduleModel(BaseModel):
    __tablename__ = "week_schedule"

    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete='CASCADE'), nullable=False)

    week_number = Column(Integer, nullable=False)
    lesson_date = Column(DateTime(timezone=True), nullable=False)

class WeeksModel(BaseModel):
    __tablename__ = "weeks"

    level = Column(Enum('Upper-Intermediate', 'IELTS', name='level_enum'), nullable=False)
    week_number = Column(Integer, index=True, nullable=False)
    week_topic = Column(String(100), nullable=True)

    essential_book = Column(UUID, ForeignKey('essential_books.id', ondelete='SET NULL'))
    essential_from_unit = Column(Integer, index=True, nullable=False)
    essential_to_unit = Column(Integer, index=True, nullable=False)

    murphy_book = Column(UUID, ForeignKey('murphy_books.id', ondelete='SET NULL'))
    murphy_from_unit = Column(Integer, index=True, nullable=False)
    murphy_to_unit = Column(Integer, index=True, nullable=False)

    keys = Column(Integer, default=10, nullable=False)

class EssentialBooksModel(BaseModel):
    __tablename__ = 'essential_books'

    book_number = Column(Integer, nullable=False)

    units = relationship(
        'EssentialUnitsModel',
        back_populates='book',
        cascade='all, delete-orphan'
    )

class EssentialUnitsModel(BaseModel):
    __tablename__ = 'essential_units'

    unit_number = Column(Integer, nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey('essential_books.id', ondelete='CASCADE'))

    book = relationship('EssentialBooksModel', back_populates='units')
    words = relationship(
        'EssentialWordsModel',
        back_populates='unit',
        cascade='all, delete-orphan'
    )

    results = relationship('StudentResultsModel', back_populates='vocabulary_unit')

class EssentialWordsModel(BaseModel):
    __tablename__ = 'essential_words'

    word = Column(String(50), nullable=False)
    meaning = Column(Text, nullable=False)
    translation_uz = Column(Text, nullable=False)
    translation_ru = Column(Text, nullable=False)

    unit_id = Column(UUID(as_uuid=True), ForeignKey('essential_units.id', ondelete='CASCADE'))
    book_id = Column(UUID(as_uuid=True), ForeignKey('essential_books.id', ondelete='CASCADE'))

    photo = Column(Text, nullable=False, default='https://file-server-nq5amwku13ul7m3x.inter-nation.uz/default.png')

    unit = relationship('EssentialUnitsModel', back_populates='words')
    results = relationship('StudentResultsModel', back_populates='vocabulary')

class MurphyBooksModel(BaseModel):
    __tablename__ = 'murphy_books'

    book_name = Column(String(150), nullable=False)

    units = relationship(
        'MurphyUnitsModel',
        back_populates='book',
        cascade='all, delete-orphan',
        order_by="MurphyUnitsModel.unit_number"
    )

class MurphyUnitsModel(BaseModel):
    __tablename__ = 'murphy_units'

    book_id = Column(UUID, ForeignKey('murphy_books.id', ondelete='CASCADE'))
    unit_number = Column(Integer, nullable=False)

    book = relationship('MurphyBooksModel',back_populates='units')
    exercises = relationship('MurphyExercisesModel', back_populates='unit', cascade='all, delete-orphan')

class MurphyExercisesModel(BaseModel):
    __tablename__ = "murphy_exercises"

    unit_id = Column(UUID(as_uuid=True), ForeignKey("murphy_units.id"), nullable=False)
    exercise_type = Column(Integer, nullable=False)
    exercise_number = Column(Integer, nullable=False)
    condition = Column(Text, nullable=False)

    unit = relationship('MurphyUnitsModel', back_populates='exercises')
    questions = relationship('MurphyExerciseQuestionsModel', back_populates='exercise', cascade='all, delete-orphan')
    results = relationship('StudentResultsModel', back_populates='exercise')

class MurphyExerciseQuestionsModel(BaseModel):
    __tablename__ = "murphy_exercise_questions"

    exercise_id = Column(UUID(as_uuid=True), ForeignKey("murphy_exercises.id"), nullable=False)
    field = Column(JSONB, nullable=False)

    exercise = relationship('MurphyExercisesModel', back_populates='questions')
    results = relationship('StudentResultsModel', back_populates='exercise_question')