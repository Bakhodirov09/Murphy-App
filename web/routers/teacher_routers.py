from datetime import datetime

from fastapi import APIRouter, Depends, status, Request, Query
from uuid import UUID

from sqlalchemy.orm import selectinload

from web.general import JWTBearer, db_dependency, decode_jwt
from web.models import GroupsModel, WeeksModel, WeekScheduleModel, EssentialUnitsModel, MurphyUnitsModel, \
    StudentResultsModel, EssentialBooksModel, EssentialWordsModel, MurphyBooksModel, MurphyExercisesModel, \
    MurphyExerciseQuestionsModel
from web.general import templates
from web.schemas import AddWeekSchema, AddWordSchema, AddEssentialUnitSchema, AddExerciseSchema, \
    AddExerciseQuestionSchema

router = APIRouter(tags=['Teacher Routers'], dependencies=[Depends(JWTBearer(type='teacher'))])

@router.get('/dashboard', status_code=status.HTTP_200_OK)
async def teacher_dashboard(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/dashboard.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/weeks', status_code=status.HTTP_200_OK)
async def weeks(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/weeks.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/exercises', status_code=status.HTTP_200_OK)
async def get_exercises_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/books.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/exercise', status_code=status.HTTP_200_OK)
async def exercise(request: Request, db: db_dependency, id: UUID = Query(...)):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/exercise.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/get-exercise', status_code=status.HTTP_200_OK)
async def get_exercise(db: db_dependency, id: UUID = Query(...)):
    exercise = db.query(MurphyExercisesModel).filter(
        MurphyExercisesModel.id == id
    ).options(selectinload(MurphyExercisesModel.questions)).first()
    return {'success': True, 'exercise': exercise}

@router.get('/add-separately-choose-the-correct-alternative', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/separately_choose_the_correct_alternative.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-choose-the-correct-alternative', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/choose_the_correct_alternative.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-fill-the-gap', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/fill_the_gap.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-separately-fill-the-gap', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/separately_fill_the_gap.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-matching', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/matching.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-word-order', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/word_order.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-complete-the-sentences', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/complete_the_sentences.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-separately-complete-the-sentences', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/complete_the_sentences.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-rewrite-the-sentences', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/rewrite_the_sentences.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/separately-choose-the-correct-alternative', status_code=status.HTTP_200_OK)
async def question_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/choose_the_correct_alternative.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/get-murphy-books', status_code=status.HTTP_200_OK)
async def get_murphy_books(db: db_dependency):
    books = db.query(MurphyBooksModel).all()
    return {'success': True, 'books': books}

@router.get('/get-book', status_code=status.HTTP_200_OK)
async def get_book(db: db_dependency, book_id: UUID = Query(...)):
    book = db.query(MurphyBooksModel).filter(
        MurphyBooksModel.id == book_id
    ).options(selectinload(MurphyBooksModel.units).options(selectinload(MurphyUnitsModel.exercises))).first()
    return {'success': True, 'book': book}

@router.post('/add-murphy-book', status_code=status.HTTP_201_CREATED)
async def add_murpy_book(request: Request, db: db_dependency):
    json = await request.json()
    book = MurphyBooksModel(
        book_name=json['name']
    )
    db.add(book)
    db.commit()
    return {'success': True}

@router.post('/add-book-unit', status_code=status.HTTP_201_CREATED)
async def add_book_unit(request: Request, db: db_dependency):
    json = await request.json()
    unit = MurphyUnitsModel(
        book_id=json['book_id'],
        unit_number=json['unit']
    )
    db.add(unit)
    db.commit()
    return {'success': True}

@router.post('/add-exercise', status_code=status.HTTP_201_CREATED)
async def add_exercises(data: AddExerciseSchema, db: db_dependency):
    exercise = MurphyExercisesModel(
        unit_id=data.unit_id,
        exercise_type=data.type,
        condition=data.condition,
        exercise_number=data.exercise_number
    )
    db.add(exercise)
    db.flush()
    db.commit()
    return {'success': True, 'exercise_id': exercise.id}

@router.get('/get-exercise', status_code=status.HTTP_200_OK)
async def get_exercise(db: db_dependency, id: UUID = Query(...)):
    exercise = db.query(MurphyExercisesModel).filter(
        MurphyExercisesModel.id == id
    ).options(selectinload(MurphyExercisesModel.questions)).first()

    return {'success': True, 'exercise': exercise}

@router.post('/add-question', status_code=status.HTTP_201_CREATED)
async def add_question(data: AddExerciseQuestionSchema, db: db_dependency):
    question = MurphyExerciseQuestionsModel(
        exercise_id=data.exercise_id,
        field=data.field
    )
    db.add(question)
    db.commit()
    return {'success': True}

@router.get('/vocabularies', status_code=status.HTTP_200_OK)
async def get_exercises_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/vocabularies.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/essential-books', status_code=status.HTTP_200_OK)
async def get_books(db: db_dependency):
    books = db.query(EssentialBooksModel).all()
    return {'success': True, 'books': books}

@router.get('/get-essential-book', status_code=status.HTTP_200_OK)
async def get_essential_book(db: db_dependency, book_id: UUID = Query(...)):
    book = db.query(EssentialBooksModel).filter(
        EssentialBooksModel.id == book_id
    ).options(
        selectinload(EssentialBooksModel.units).selectinload(EssentialUnitsModel.words)
    ).first()
    return {'success': True, 'book': book}

@router.post('/add-essential-book', status_code=status.HTTP_201_CREATED)
async def add_book(request: Request, db: db_dependency):
    json = await request.json()
    book = EssentialBooksModel(
        book_number=json['number']
    )
    db.add(book)
    db.commit()
    return {'success': True}

@router.post('/add-essential-unit', status_code=status.HTTP_201_CREATED)
async def add_essential_unit(data: AddEssentialUnitSchema, db: db_dependency):
    unit = EssentialUnitsModel(
        book_id=data.book_id,
        unit_number=data.unit_number
    )
    db.add(unit)
    db.commit()
    return {'success': True}

@router.post('/add-word', status_code=status.HTTP_201_CREATED)
async def add_word(data: AddWordSchema, db: db_dependency):
    word = EssentialWordsModel(
        word=data.word,
        meaning=data.meaning,
        translation_uz=data.translation_uz,
        translation_ru=data.translation_ru,
        unit_id=data.unit_id,
        book_id=data.book_id
    )
    db.add(word)
    db.commit()
    return {'success': True}

@router.get('/level-weeks', status_code=status.HTTP_200_OK)
async def get_level_weeks(db: db_dependency, level: str = Query(...)):
    weeks = db.query(WeeksModel).filter(
        WeeksModel.level == level
    ).all()
    return {'success': True, 'weeks': weeks}

@router.get('/get-clear-groups', status_code=status.HTTP_200_OK)
async def get_clear_groups(db: db_dependency, days: str = Query(...)):
    groups = db.query(GroupsModel).filter(GroupsModel.group_days == days).all()
    return {'success': True, 'groups': groups}

@router.get('/get-group-results', status_code=status.HTTP_200_OK)
async def get_group_students(month: str, db: db_dependency, id: UUID = Query(...)):
    students = db.query(GroupsModel).filter(GroupsModel.id == id).first()
    start_date = datetime.strptime(month, '%Y-%m')
    now = datetime.now()
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)
    effective_end_date = min(end_date, now)
    week_schedule = (
        db.query(WeekScheduleModel)
        .filter(
            WeekScheduleModel.group_id == id,
            WeekScheduleModel.lesson_date >= start_date,
            WeekScheduleModel.lesson_date < end_date
        )
        .all()
    )
    available_week_schedule = db.query(WeekScheduleModel).filter(
        WeekScheduleModel.group_id == id,
        WeekScheduleModel.lesson_date >= start_date,
        WeekScheduleModel.lesson_date <= effective_end_date
    ).all()
    students_copy = list()
    for student in students.students:
        student_copy = student.__dict__.copy()
        student_copy['progress'] = list()
        for week_s in available_week_schedule:
            week = db.query(WeeksModel).filter(WeeksModel.week_number == week_s.week_number).first()
            murphy_units = db.query(MurphyUnitsModel).filter(
                MurphyUnitsModel.unit_number >= week.murphy_from_unit,
                MurphyUnitsModel.unit_number <= week.murphy_to_unit
            ).all()
            vocabularies = db.query(EssentialUnitsModel).filter(
                EssentialUnitsModel.unit_number >= week.essential_from_unit,
                EssentialUnitsModel.unit_number <= week.essential_to_unit
            ).all()
            q_count = 0
            p_count = 0
            for murphy in murphy_units:
                for e in murphy.exercises:
                    q_count += len(e.questions)
                    p_count += db.query(StudentResultsModel).filter(
                        StudentResultsModel.exercise_id == e.id,
                        StudentResultsModel.student_id == student.id,
                        StudentResultsModel.passed == True
                    ).count()
            for vocab in vocabularies:
                q_count += len(vocab.words)
                p_count += db.query(StudentResultsModel).filter(
                    StudentResultsModel.vocabulary_unit_id == vocab.id,
                    StudentResultsModel.student_id == student.id,
                    StudentResultsModel.passed == True
                ).count()
            student_copy['progress'].append({
                'week_id': week.id,
                'percent': round((p_count / q_count) * 100) if q_count != 0 else 0
            })
        students_copy.append(student_copy)
    return {'success': True, 'students': students_copy, 'schedule': week_schedule}

@router.post('/add-week', status_code=status.HTTP_200_OK)
async def add_week(data: AddWeekSchema, db: db_dependency):
    week = WeeksModel(
        week_number=data.week_number,
        level=data.level,
        essential_book=data.essential_book,
        essential_from_unit=data.essential_from_unit,
        essential_to_unit=data.essential_to_unit,
        murphy_book=data.murphy_book,
        murphy_from_unit=data.murphy_from_unit,
        murphy_to_unit=data.murphy_to_unit,
        keys=data.keys,
        week_topic=data.week_topic
    )
    db.add(week)
    db.flush()
    db.commit()
    return {'success': True}
