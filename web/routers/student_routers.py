import os
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from uuid import UUID
from sqlalchemy.orm import selectinload
from starlette.responses import HTMLResponse

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
        # HTML sahifa + cookie delete backenddan
        response_content = """
        <html>
            <body>
                <script>
                    // Oyna yopish
                    window.close();
                </script>
            </body>
        </html>
        """
        response = HTMLResponse(content=response_content, status_code=200)
        # Backenddan cookie-ni o'chirish
        response.delete_cookie(key="token", path="/")
        return response

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

    # --- Batch fetch all WeeksModel ---
    week_ids = [w.week_id for w in group_weeks]
    weeks_map = {
        w.id: w for w in db.query(WeeksModel).filter(WeeksModel.id.in_(week_ids)).all()
    }

    available_week_infos = [
        weeks_map[w.week_id] for w in group_weeks
        if w.lesson_date <= today and w.week_id in weeks_map
    ]

    # --- Batch fetch books to know IELTS vs Murphy ---
    book_ids = list({wi.book for wi in available_week_infos if wi.book})
    books_map = {
        b.id: b for b in db.query(BooksModel).filter(BooksModel.id.in_(book_ids)).all()
    } if book_ids else {}

    ielts_week_infos  = [wi for wi in available_week_infos if books_map.get(wi.book) and books_map[wi.book].level == LevelsEnum.IELTS]
    murphy_week_infos = [wi for wi in available_week_infos if books_map.get(wi.book) and books_map[wi.book].level != LevelsEnum.IELTS]

    # --- Batch fetch Murphy: units -> exercises -> questions ---
    murphy_units_all = []
    for wi in murphy_week_infos:
        murphy_units_all += db.query(UnitsModel).options(
            selectinload(UnitsModel.exercises).selectinload(ExercisesModel.questions)
        ).filter(
            UnitsModel.book_id == wi.book,
            UnitsModel.unit_number >= wi.book_from_unit,
            UnitsModel.unit_number <= wi.book_to_unit,
        ).all()

    # --- Batch fetch IELTS: tests -> sections ---
    ielts_tests_all = []
    for wi in ielts_week_infos:
        ielts_tests_all += db.query(IELTSTestsModel).options(
            selectinload(IELTSTestsModel.sections)
        ).filter(
            IELTSTestsModel.book_id == wi.book,
            IELTSTestsModel.test_number >= wi.book_from_unit,
            IELTSTestsModel.test_number <= wi.book_to_unit,
        ).all()

    # --- Batch fetch Vocab: essential units -> words ---
    vocab_units_all = []
    for wi in available_week_infos:
        vocab_units_all += db.query(EssentialUnitsModel).options(
            selectinload(EssentialUnitsModel.words)
        ).filter(
            EssentialUnitsModel.book_id == wi.essential_book,
            EssentialUnitsModel.unit_number >= wi.essential_from_unit,
            EssentialUnitsModel.unit_number <= wi.essential_to_unit,
        ).all()

    # --- Collect all IDs for batch result queries ---
    all_question_ids = [q.id for u in murphy_units_all for e in u.exercises for q in e.questions]
    all_section_ids  = [s.id for t in ielts_tests_all for s in t.sections]
    all_word_ids     = [w.id for u in vocab_units_all for w in u.words]

    # --- 3 queries total for ALL student results ---
    passed_question_ids = set()
    passed_section_ids  = set()
    passed_vocab_ids    = set()

    if all_question_ids:
        rows = db.query(StudentResultsModel.exercise_question_id).filter(
            StudentResultsModel.student_id == student.id,
            StudentResultsModel.exercise_question_id.in_(all_question_ids),
            StudentResultsModel.passed == True,
        ).all()
        passed_question_ids = {r[0] for r in rows}

    if all_section_ids:
        rows = db.query(StudentResultsModel.ielts_section_id).filter(
            StudentResultsModel.student_id == student.id,
            StudentResultsModel.ielts_section_id.in_(all_section_ids),
            StudentResultsModel.passed == True,
        ).all()
        passed_section_ids = {r[0] for r in rows}

    if all_word_ids:
        rows = db.query(StudentResultsModel.vocabulary_id).filter(
            StudentResultsModel.student_id == student.id,
            StudentResultsModel.vocabulary_id.in_(all_word_ids),
            StudentResultsModel.passed == True,
        ).all()
        passed_vocab_ids = {r[0] for r in rows}

    # --- Build per-week lookups (pure Python, no DB) ---
    murphy_units_by_week = {
        wi.id: [u for u in murphy_units_all
                if u.book_id == wi.book and wi.book_from_unit <= u.unit_number <= wi.book_to_unit]
        for wi in murphy_week_infos
    }
    ielts_tests_by_week = {
        wi.id: [t for t in ielts_tests_all
                if t.book_id == wi.book and wi.book_from_unit <= t.test_number <= wi.book_to_unit]
        for wi in ielts_week_infos
    }
    vocab_units_by_week = {
        wi.id: [u for u in vocab_units_all
                if u.book_id == wi.essential_book and wi.essential_from_unit <= u.unit_number <= wi.essential_to_unit]
        for wi in available_week_infos
    }

    # --- Build final result ---
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
            "progress": 0,
        }

        if is_available:
            correct_count = 0
            overall = 0
            book = books_map.get(week_info.book)
            is_ielts = book and book.level == LevelsEnum.IELTS

            if is_ielts:
                # IELTS: 1 section = 1 unit of progress
                for test in ielts_tests_by_week.get(week_info.id, []):
                    for section in test.sections:
                        overall += 1
                        if section.id in passed_section_ids:
                            correct_count += 1
            else:
                # Murphy: 1 question = 1 unit of progress
                for unit in murphy_units_by_week.get(week_info.id, []):
                    for e in unit.exercises:
                        overall += len(e.questions)
                        for q in e.questions:
                            if q.id in passed_question_ids:
                                correct_count += 1

            # Vocab is same for both
            for unit in vocab_units_by_week.get(week_info.id, []):
                overall += len(unit.words)
                for w in unit.words:
                    if w.id in passed_vocab_ids:
                        correct_count += 1

            if overall:
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
    student_id = decoded_token['student_id']

    week = db.query(WeeksModel).filter(WeeksModel.id == id).first()
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    is_ielts = week.level == LevelsEnum.IELTS

    # --- Fetch vocab units + words ---
    vocabulary_units = (
        db.query(EssentialUnitsModel)
        .options(selectinload(EssentialUnitsModel.words))
        .filter(
            EssentialUnitsModel.book_id == week.essential_book,
            EssentialUnitsModel.unit_number >= week.essential_from_unit,
            EssentialUnitsModel.unit_number <= week.essential_to_unit,
        )
        .all()
    )

    # --- Fetch murphy/ielts units ---
    if is_ielts:
        units = (
            db.query(IELTSTestsModel)
            .options(
                selectinload(IELTSTestsModel.sections)
                .selectinload(IELTSSectionsModel.questions)
            )
            .filter(
                IELTSTestsModel.book_id == week.book,  # ✅ was missing!
                IELTSTestsModel.test_number >= week.book_from_unit,
                IELTSTestsModel.test_number <= week.book_to_unit,
            )
            .all()
        )
        all_sections = [s for t in units for s in t.sections]
    else:
        units = (
            db.query(UnitsModel)
            .options(
                selectinload(UnitsModel.exercises)
                .selectinload(ExercisesModel.questions)
            )
            .filter(
                UnitsModel.book_id == week.book,
                UnitsModel.unit_number >= week.book_from_unit,
                UnitsModel.unit_number <= week.book_to_unit,
            )
            .all()
        )
        all_sections = [e for u in units for e in u.exercises]

    # --- Batch fetch ALL student results at once ---
    all_vocab_unit_ids = [v.id for v in vocabulary_units]
    all_section_ids    = [s.id for s in all_sections]

    passed_vocab_results: dict[UUID, list] = {v_id: [] for v_id in all_vocab_unit_ids}
    if all_vocab_unit_ids:
        vocab_results = db.query(StudentResultsModel).filter(
            StudentResultsModel.student_id == student_id,
            StudentResultsModel.vocabulary_unit_id.in_(all_vocab_unit_ids),
            StudentResultsModel.passed == True,
        ).all()
        for r in vocab_results:
            passed_vocab_results[r.vocabulary_unit_id].append(r)

    passed_exercise_results: dict[UUID, list] = {s_id: [] for s_id in all_section_ids}
    if all_section_ids:
        if is_ielts:
            exercise_results = db.query(StudentResultsModel).filter(
                StudentResultsModel.student_id == student_id,
                StudentResultsModel.ielts_section_id.in_(all_section_ids),
                StudentResultsModel.passed == True,
            ).all()
            for r in exercise_results:
                passed_exercise_results[r.ielts_section_id].append(r)
        else:
            exercise_results = db.query(StudentResultsModel).filter(
                StudentResultsModel.student_id == student_id,
                StudentResultsModel.exercise_id.in_(all_section_ids),
                StudentResultsModel.passed == True,
            ).all()
            for r in exercise_results:
                passed_exercise_results[r.exercise_id].append(r)

    # --- Build vocabularies ---
    vocabularies = []
    for vocab_unit in vocabulary_units:
        results = passed_vocab_results.get(vocab_unit.id, [])
        word_count = len(vocab_unit.words)
        percent = round((len(results) / word_count) * 100) if word_count else 0
        vocabularies.append({
            'id': vocab_unit.id,
            'words': vocab_unit.words,
            'percent': percent,
        })

    # --- Build murphy/ielts exercises ---
    murphy_exercises = []
    for section in all_sections:
        # Skip not-ready IELTS sections
        if hasattr(section, 'status') and section.status != 'ready':
            continue

        results = passed_exercise_results.get(section.id, [])

        if is_ielts:
            # ✅ For IELTS: section is either passed or not = 100 or 0
            percent = 100 if results else 0
        else:
            q_count = len(section.questions)
            percent = round((len(results) / q_count) * 100) if q_count else 0

        murphy_exercises.append({
            'id': section.id,
            'percent': percent,
        })

    return {
        'success': True,
        'week': week.week_number,
        'vocabularies': vocabularies,
        'murphy_exercises': murphy_exercises,
    }

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

@router.get('/reading', status_code=status.HTTP_200_OK)
async def get_reading(request: Request):
    return templates.TemplateResponse('/students/reading.html', {
        'request': request,
    })
