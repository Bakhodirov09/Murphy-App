from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from uuid import UUID

from sqlalchemy.orm import selectinload

from web.data import tashkent
from web.general import db_dependency, create_token, decode_jwt, JWTBearer, templates
from web.schemas import GroupDaysRequest, SaveResultsSchema
from web.models import GroupsModel, StudentsModel, WeeksModel, WeekScheduleModel, MurphyUnitsModel, EssentialUnitsModel, \
    MurphyExercisesModel, MurphyBooksModel, StudentResultsModel

router = APIRouter(dependencies=[Depends(JWTBearer(type='student'))])


async def get_first_lesson_date(months_ago: int, weekday: int):
    target_month = (datetime.now(tashkent) - relativedelta(months=months_ago)).replace(day=1)
    offset = (weekday - target_month.weekday()) % 7

    return target_month + timedelta(days=offset)

@router.get('/dashboard', status_code=status.HTTP_200_OK)
async def dashboard(db: db_dependency, request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    student = db.query(StudentsModel).filter(
        StudentsModel.id == decoded_token['student_id']
    ).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'success': False, 'message': 'User Not Found'})
    return templates.TemplateResponse('/students/dashboard.html', {
        'request': request,
        'level': decoded_token['level'],
        'photo': student.avatar_url
    })

@router.post('/ok', status_code=status.HTTP_201_CREATED)
async def ok(request: Request, db: db_dependency):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    student = StudentsModel(
        first_name=decoded_token['user']['first_name'],
        last_name=decoded_token['user']['last_name'],
        avatar_url=decoded_token['user']['avatar_url']
    )
    db.add(student)
    group = db.query(GroupsModel).filter(GroupsModel.group_name == decoded_token['user']['group']).first()
    db.flush()
    new_token = await create_token({'student_id': str(student.id), 'type': 'student', 'level': decoded_token['user']['level'], 'sub': decoded_token['user']['sub']})
    if group:
        student.group_id = group.id
        db.commit()
    else:
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'message': 'Group not found', 'new_token': new_token, 'group': decoded_token['user']['group']})
    return {
        'new_token': new_token
    }

@router.post('/create-group', status_code=status.HTTP_201_CREATED)
async def create_group(request: Request, data: GroupDaysRequest, db: db_dependency):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    new_group = GroupsModel(
        group_name=data.group,
        group_days='Odd Days' if data.days == 0 else 'Even Days',
        group_level=data.level
    )
    db.add(new_group)
    db.flush()
    db.refresh(new_group)
    student = db.query(StudentsModel).filter(StudentsModel.id == decoded_token['student_id']).first()
    student.group_id = new_group.id
    db.commit()

    weeks = db.query(WeeksModel).filter(WeeksModel.level == decoded_token['level']).all()
    week_day = 2 if data.days == 0 else 1
    first_lesson = await get_first_lesson_date(0, week_day)
    if decoded_token['level'] in ['Intermediate', 'Upper-Intermediate']:
        if decoded_token['sub'] == 'Middle':
            first_lesson = await get_first_lesson_date(1, week_day)
        elif decoded_token['sub'] == 'Final':
            first_lesson = await get_first_lesson_date(2, week_day)
    elif decoded_token['level'] == 'IELTS':
        if decoded_token['sub'] == 'Middle 1':
            first_lesson = await get_first_lesson_date(1, week_day)
        elif decoded_token['sub'] == 'Middle 2':
            first_lesson = await get_first_lesson_date(2, week_day)
        elif decoded_token['sub'] == 'Final':
            first_lesson = await get_first_lesson_date(3, week_day)
    for i in range(1, len(weeks) + 1):
        schedule = WeekScheduleModel(
            group_id=new_group.id,
            week_number=i,
            lesson_date=first_lesson + timedelta(weeks=i - 1)
        )
        db.add(schedule)

        db.commit()
    return {
        'ok': True
    }

@router.get('/get-weeks', status_code=status.HTTP_200_OK)
async def get_student_weeks(request: Request, db: db_dependency):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    student = db.query(StudentsModel).filter(
        StudentsModel.id == decoded_token['student_id']
    ).first()
    group_weeks = db.query(WeekScheduleModel).filter(
        WeekScheduleModel.group_id == student.group_id
    ).all()
    today = datetime.now(tz=tashkent)
    result = list()

    for week in group_weeks:
        is_available = week.lesson_date <= today

        week_info = db.query(WeeksModel).filter(
            WeeksModel.week_number == week.week_number
        ).first()

        week_data = {
            "id": week_info.id,
            "lesson_date": week.lesson_date,
            "week_number": week.week_number,
            "is_available": is_available,
            "progress": 0
        }
        if is_available:

            murphy_units = db.query(MurphyUnitsModel).filter(
                MurphyUnitsModel.book_id == week_info.murphy_book,
                MurphyUnitsModel.unit_number >= week_info.murphy_from_unit,
                MurphyUnitsModel.unit_number <= week_info.murphy_to_unit,
            ).all()

            correct_count = 0
            overall_questions_words = 0
            for unit in murphy_units:
                for e in unit.exercises:
                    overall_questions_words += len(e.questions)
                    for q in e.questions:
                        sr = db.query(StudentResultsModel).filter(
                            StudentResultsModel.student_id == student.id,
                            StudentResultsModel.exercise_question_id == q.id,
                            StudentResultsModel.passed == True
                        ).first()
                        if sr:
                            correct_count += 1

            vocab_units = db.query(EssentialUnitsModel).filter(
                EssentialUnitsModel.book_id == week_info.essential_book,
                EssentialUnitsModel.unit_number >= week_info.essential_from_unit,
                EssentialUnitsModel.unit_number <= week_info.essential_to_unit,
            ).all()
            for unit in vocab_units:
                for w in unit.words:
                    overall_questions_words += len(w.questions)
                    sr = db.query(StudentResultsModel).filter(
                        StudentResultsModel.student_id == student.id,
                        StudentResultsModel.vocabulary_id == w.id,
                        StudentResultsModel.passed == True
                    ).first()
                    if sr:
                        correct_count += 1
            progress = 0
            if correct_count != 0:
                progress = round((correct_count / overall_questions_words) * 100)
            week_data['progress'] = progress
        result.append(week_data)

    return {'success': True, 'student': student, 'weeks': result}

@router.get('/week', status_code=status.HTTP_200_OK)
async def week(request: Request):
    return templates.TemplateResponse('/students/week.html', {
        'request': request
    })

@router.get('/get-week', status_code=status.HTTP_200_OK)
async def get_week(request: Request, db: db_dependency, id: UUID = Query(...)):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    week = db.query(WeeksModel).filter(WeeksModel.id == id).first()
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    murphy_units = db.query(MurphyUnitsModel).filter(
        MurphyUnitsModel.book_id == week.murphy_book,
        MurphyUnitsModel.unit_number >= week.murphy_from_unit,
        MurphyUnitsModel.unit_number <= week.murphy_to_unit,
    )
    vocabulary_units = db.query(EssentialUnitsModel).filter(
        EssentialUnitsModel.book_id == week.essential_book,
        EssentialUnitsModel.unit_number >= week.essential_from_unit,
        EssentialUnitsModel.unit_number <= week.essential_to_unit,
    )
    vocabularies = list()
    murphy_exercises = list()
    for vocabulary in vocabulary_units:
        results = db.query(StudentResultsModel).filter(
            StudentResultsModel.student_id == decoded_token['student_id'],
            StudentResultsModel.vocabulary_unit_id == vocabulary.id
        ).all()
        vocabularies.append({'id': vocabulary.id, 'words': vocabulary.words, 'percent': round((len(results) / len(vocabulary.words)) * 100)})
    for murphy in murphy_units:
        for e in murphy.exercises:
            results = db.query(StudentResultsModel).filter(
                StudentResultsModel.student_id == decoded_token['student_id'],
                StudentResultsModel.exercise_id == e.id,
                StudentResultsModel.passed == True,
            ).all()
            murphy_exercises.append({'id': e.id, 'percent': round((len(results) / len(e.questions)) * 100)})
    return {'success': True, 'week': week.week_number, 'vocabularies': vocabularies, 'murphy_exercises': murphy_exercises}

@router.get('/exercise', status_code=status.HTTP_200_OK)
async def exercise_page(request: Request):
    return templates.TemplateResponse('/students/exercise.html', {
        'request': request,
        'answerKey': '{%answer%}'
    })

@router.get('/get-exercise', status_code=status.HTTP_200_OK)
async def get_exercise(db: db_dependency, id: UUID = Query(...)):
    exercise = db.query(MurphyExercisesModel).filter(
        MurphyExercisesModel.id == id
    ).options(selectinload(MurphyExercisesModel.questions)).first()

    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return {'success': True, 'exercise': exercise}

@router.post('/save-exercise-results', status_code=status.HTTP_200_OK)
async def save_results(request: Request, data: SaveResultsSchema, db: db_dependency):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    for result in data.results:
        old_result = db.query(StudentResultsModel).filter(
            StudentResultsModel.student_id == decoded_token['student_id'],
            StudentResultsModel.week_id == data.week_id,
            StudentResultsModel.exercise_id == data.exercise_id,
            StudentResultsModel.exercise_question_id == result.question_id
        ).first()
        if not old_result:
            student_result = StudentResultsModel(
                student_id=decoded_token['student_id'],
                week_id=data.week_id,
                type='Exercise',
                exercise_id=data.exercise_id,
                exercise_question_id=result.question_id
            )
            if result.failed:
                student_result.fails_count = 1
            else:
                student_result.passed = True
            db.add(student_result)
        elif old_result.passed == False:
            if result.failed:
                old_result.fails_count = old_result.fails_count + 1
            else:
                old_result.passed = True
        db.commit()

    return {'ok': True}
