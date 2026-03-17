import os
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from uuid import UUID
from sqlalchemy.orm import selectinload

from web.data import tashkent
from web.general import db_dependency, create_token, decode_jwt, JWTBearer, templates, check_student_answer, clean_text
from web.schemas import GroupDaysRequest, SaveResultsSchema, SaveVocabResultsSchema, CheckDictationSchema
from web.models import GroupsModel, StudentsModel, WeeksModel, WeekScheduleModel, UnitsModel, EssentialUnitsModel, \
    ExercisesModel, BooksModel, StudentResultsModel, FilesModel, IELTSSectionsModel, LevelsEnum, IELTSTestsModel

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
        'photo': student.avatar_url,
        'first_name': student.first_name
    })

@router.get('/settings', status_code=status.HTTP_200_OK)
async def dashboard(db: db_dependency, request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    student = db.query(StudentsModel).filter(
        StudentsModel.id == decoded_token['student_id']
    ).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'success': False, 'message': 'User Not Found'})
    return templates.TemplateResponse('/students/settings.html', {
        'request': request,
        'level': decoded_token['level'],
        'photo': student.avatar_url,
        'first_name': student.first_name
    })


@router.post('/ok', status_code=status.HTTP_201_CREATED)
async def ok(request: Request, db: db_dependency):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)

    chat_id = decoded_token['user']['chat_id']

    student = db.query(StudentsModel).filter(
        StudentsModel.chat_id == chat_id
    ).first()

    if not student:
        student = StudentsModel(
            first_name=decoded_token['user']['first_name'],
            last_name=decoded_token['user']['last_name'],
            avatar_url=decoded_token['user']['avatar_url'],
            chat_id=chat_id,
        )
        db.add(student)
        db.flush()

    group = db.query(GroupsModel).filter(
        GroupsModel.group_name == decoded_token['user']['group']
    ).first()

    new_token = await create_token({
        'student_id': str(student.id),
        'type': 'student',
        'level': decoded_token['user']['level'],
        'sub': decoded_token['user']['sub'],
        'group': decoded_token['user']['group']
    })
    db.commit()

    if not group:
        resp = JSONResponse(
            {'message': 'Group not found'},
            status_code=status.HTTP_404_NOT_FOUND
        )
        resp.set_cookie(key='token', value=new_token, httponly=True,
                        max_age=60*60*24*15, path='/', samesite='lax')
        return resp

    student.group_id = group.id
    db.commit()

    resp = JSONResponse({'ok': True}, status_code=status.HTTP_201_CREATED)
    resp.set_cookie(key='token', value=new_token, httponly=True,
                    max_age=60*60*24*15, path='/', samesite='lax')
    return resp

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

    weeks = db.query(WeeksModel).filter(WeeksModel.level == decoded_token['level']).order_by(WeeksModel.week_number).all()
    week_day = 2 if data.days == 0 else 1
    first_lesson = await get_first_lesson_date(0, week_day)
    if decoded_token['level'] in 'Upper-Intermediate':
        if decoded_token['sub'] == 'Middle':
            first_lesson = await get_first_lesson_date(1, week_day)
        elif decoded_token['sub'] == 'Final':
            first_lesson = await get_first_lesson_date(2, week_day)
    elif decoded_token['level'] == 'IELTS':
        if decoded_token['sub'] == 'Start':
            first_lesson = await get_first_lesson_date(1, week_day)
        elif decoded_token['sub'] == 'Middle':
            first_lesson = await get_first_lesson_date(2, week_day)
        elif decoded_token['sub'] == 'Middle 2':
            first_lesson = await get_first_lesson_date(3, week_day)
        elif decoded_token['sub'] == 'Final':
            first_lesson = await get_first_lesson_date(4, week_day)
    for i, w in enumerate(weeks, start=1):
        schedule = WeekScheduleModel(
            group_id=new_group.id,
            week_number=i,
            week_id=w.id,
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

    # --- Batch fetch all WeeksModel at once ---
    week_ids = [w.week_id for w in group_weeks]
    weeks_map = {
        w.id: w for w in db.query(WeeksModel).filter(WeeksModel.id.in_(week_ids)).all()
    }

    # --- Collect available weeks only ---
    available_week_infos = [
        weeks_map[w.week_id] for w in group_weeks
        if w.lesson_date <= today and w.week_id in weeks_map
    ]

    # --- Batch fetch all murphy UnitsModel ---
    from sqlalchemy import and_, or_, tuple_
    # Build all (book_id, from, to) ranges
    murphy_units_all = []
    vocab_units_all = []

    for wi in available_week_infos:
        murphy_units_all += db.query(UnitsModel).filter(
            UnitsModel.book_id == wi.book,
            UnitsModel.unit_number >= wi.book_from_unit,
            UnitsModel.unit_number <= wi.book_to_unit,
        ).all()

        vocab_units_all += db.query(EssentialUnitsModel).filter(
            EssentialUnitsModel.book_id == wi.essential_book,
            EssentialUnitsModel.unit_number >= wi.essential_from_unit,
            EssentialUnitsModel.unit_number <= wi.essential_to_unit,
        ).all()

    # --- Collect all question IDs and word IDs ---
    all_question_ids = [
        q.id
        for unit in murphy_units_all
        for e in unit.exercises
        for q in e.questions
    ]
    all_word_ids = [
        w.id
        for unit in vocab_units_all
        for w in unit.words
    ]

    # --- Single query for all StudentResults ---
    passed_question_ids = set()
    passed_vocab_ids = set()

    if all_question_ids:
        rows = db.query(StudentResultsModel.exercise_question_id).filter(
            StudentResultsModel.student_id == student.id,
            StudentResultsModel.exercise_question_id.in_(all_question_ids),
            StudentResultsModel.passed == True
        ).all()
        passed_question_ids = {r[0] for r in rows}

    if all_word_ids:
        rows = db.query(StudentResultsModel.vocabulary_id).filter(
            StudentResultsModel.student_id == student.id,
            StudentResultsModel.vocabulary_id.in_(all_word_ids),
            StudentResultsModel.passed == True
        ).all()
        passed_vocab_ids = {r[0] for r in rows}

    # --- Build per-week unit/word lookup ---
    # Map week_info.id -> its units/words
    murphy_units_by_week: dict[int, list] = {}
    vocab_units_by_week: dict[int, list] = {}

    for wi in available_week_infos:
        murphy_units_by_week[wi.id] = [
            unit for unit in murphy_units_all
            if unit.book_id == wi.book
            and wi.book_from_unit <= unit.unit_number <= wi.book_to_unit
        ]
        vocab_units_by_week[wi.id] = [
            unit for unit in vocab_units_all
            if unit.book_id == wi.essential_book
            and wi.essential_from_unit <= unit.unit_number <= wi.essential_to_unit
        ]

    # --- Build result ---
    result = []
    for week in group_weeks:
        is_available = week.lesson_date <= today
        week_info = weeks_map.get(week.week_id)
        if not week_info:
            continue

        week_data = {
            "id": week_info.id,
            "lesson_date": week.lesson_date,
            "week_number": week.week_number,
            "is_available": is_available,
            "topic": week_info.week_topic,
            "progress": 0
        }

        if is_available:
            correct_count = 0
            overall = 0

            for unit in murphy_units_by_week.get(week_info.id, []):
                for e in unit.exercises:
                    overall += len(e.questions)
                    for q in e.questions:
                        if q.id in passed_question_ids:
                            correct_count += 1

            for unit in vocab_units_by_week.get(week_info.id, []):
                word_count = len(unit.words)
                overall += word_count
                for w in unit.words:
                    if w.id in passed_vocab_ids:
                        correct_count += 1

            if correct_count and overall:
                week_data['progress'] = round((correct_count / overall) * 100)

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
    if week.level == LevelsEnum.UPPER_INTERMEDIATE:
        murphy_units = db.query(UnitsModel).filter(
            UnitsModel.book_id == week.book,
            UnitsModel.unit_number >= week.book_from_unit,
            UnitsModel.unit_number <= week.book_to_unit,
        )
    else:
        murphy_units = db.query(IELTSTestsModel).filter(
            IELTSTestsModel.test_number >= week.book_from_unit,
            IELTSTestsModel.test_number <= week.book_to_unit,
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
            StudentResultsModel.vocabulary_unit_id == vocabulary.id,
            StudentResultsModel.passed == True
        ).all()
        vocabularies.append({'id': vocabulary.id, 'words': vocabulary.words, 'percent': round((len(results) / len(vocabulary.words)) * 100)})
    for murphy in murphy_units:
        exercises = murphy.sections if hasattr(murphy, 'sections') else murphy.exercises
        for e in exercises:
            if week.level == LevelsEnum.UPPER_INTERMEDIATE:
                results = db.query(StudentResultsModel).filter(
                    StudentResultsModel.student_id == decoded_token['student_id'],
                    StudentResultsModel.exercise_id == e.id,
                    StudentResultsModel.passed == True,
                ).all()
            else:
                results = db.query(StudentResultsModel).filter(
                    StudentResultsModel.student_id == decoded_token['student_id'],
                    StudentResultsModel.ielts_section_id == e.id,
                    StudentResultsModel.passed == True,
                ).all()
            if not hasattr(e, 'status') or e.status == "ready":
                murphy_exercises.append({
                    'id': e.id,
                    'percent': round((len(results) / len(e.questions)) * 100) if e.questions else 0
                })
    return {'success': True, 'week': week.week_number, 'vocabularies': vocabularies, 'murphy_exercises': murphy_exercises}

@router.get('/exercise', status_code=status.HTTP_200_OK)
async def exercise_page(request: Request):
    return templates.TemplateResponse('/students/exercise.html', {
        'request': request,
        'answerKey': '{%answer%}'
    })

@router.get('/vocabulary', status_code=status.HTTP_200_OK)
async def vocabulary_page(request: Request):
    return templates.TemplateResponse('/students/vocabulary.html', {
        'request': request,
    })

@router.get('/get-vocabulary-words', status_code=status.HTTP_200_OK)
async def get_vocabulary_words(db: db_dependency, id: UUID = Query(...)):
    words = db.query(EssentialUnitsModel).filter(
        EssentialUnitsModel.id == id
    ).options(selectinload(EssentialUnitsModel.words)).first()
    return {'ok': True, 'words': words}

@router.get('/get-exercise', status_code=status.HTTP_200_OK)
async def get_exercise(db: db_dependency, id: UUID = Query(...), level: str = Query(default='Upper-Intermediate')):
    if level == 'Upper-Intermediate':
        exercise = db.query(ExercisesModel).filter(
            ExercisesModel.id == id
        ).options(selectinload(ExercisesModel.questions)).first()
    else:
        exercise = db.query(IELTSSectionsModel).filter(
            IELTSSectionsModel.id == id
        ).options(selectinload(IELTSSectionsModel.questions)).first()
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

@router.post('/save-vocabulary-results', status_code=status.HTTP_200_OK)
async def save_results(request: Request, data: SaveVocabResultsSchema, db: db_dependency):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    for result in data.results:
        old_result = db.query(StudentResultsModel).filter(
            StudentResultsModel.student_id == decoded_token['student_id'],
            StudentResultsModel.week_id == data.week_id,
            StudentResultsModel.vocabulary_unit_id == data.unit_id,
            StudentResultsModel.vocabulary_id == result.vocabulary_id
        ).first()
        if not old_result:
            student_result = StudentResultsModel(
                student_id=decoded_token['student_id'],
                week_id=data.week_id,
                type='Vocab',
                vocabulary_unit_id=data.unit_id,
                vocabulary_id=result.vocabulary_id
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

@router.get('/file/{file_id}', status_code=status.HTTP_200_OK)
async def get_file(db: db_dependency, file_id: UUID):
    file_db = db.query(FilesModel).filter(
        FilesModel.id == file_id
    ).first()
    if not file_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
            'ok': False,
            'message': 'File not found'
        })
    if not os.path.exists(file_db.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
            'ok': False,
            'message': 'File not found on disk'
        })
    return FileResponse(file_db.file_path)

@router.get('/dictation', status_code=status.HTTP_200_OK)
async def dictation(request: Request):
    return templates.TemplateResponse('/students/dictation.html', {
        'request': request,
    })

@router.post('/check-dictation', status_code=status.HTTP_200_OK)
async def check_dictation(request: Request, data: CheckDictationSchema, db: db_dependency):
    cookies = request.cookies
    token = cookies.get('token')
    decoded_token = await decode_jwt(token)
    if not decoded_token:
        return HTTPException(404, 'User not found')
    script = clean_text(data.script)
    result = check_student_answer(data.student_script, script, data.segments)
    old_results = db.query(StudentResultsModel).filter(
        StudentResultsModel.student_id == decoded_token['student_id'],
        StudentResultsModel.week_id == data.week_id,
        StudentResultsModel.ielts_section_id == data.section_id,
    ).first()
    if old_results:
        if result:
            old_results.fails_count = old_results.fails_count + 1
            old_results.answer_given = result
        else:
            old_results.passed = True
    else:
        result_db = StudentResultsModel(
            student_id=decoded_token['student_id'],
            week_id=data.week_id,
            type='Exercise',
            ielts_section_id=data.section_id,
            passed=not result,
            answer_given=result
        )
        if result:
            result_db.fails_count = 1
            result_db.answer_given = result
        db.add(result_db)
    db.commit()
    return {'ok': not result, 'missed': result}
