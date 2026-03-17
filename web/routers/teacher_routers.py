import shutil
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status, Request, Query, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import selectinload

from web.general import JWTBearer, db_dependency, decode_jwt, get_transcribe_with_ai
from web.general import templates
from web.models import (
    GroupsModel, WeeksModel, WeekScheduleModel,
    EssentialUnitsModel, UnitsModel, StudentResultsModel,
    EssentialBooksModel, EssentialWordsModel, BooksModel,
    ExercisesModel, ExerciseQuestionsModel, StudentsModel, FilesModel, IELTSSectionsModel, IELTSTestsModel, DaysEnum,
    IELTSModule, IELTSQuestionsModel, LevelsEnum
)
from web.schemas import (
    AddWeekSchema, AddWordSchema, AddEssentialUnitSchema,
    AddExerciseSchema, AddExerciseQuestionSchema, AddIELTSListeningSchema, AddIELTSReadingSchema,
)

router = APIRouter(dependencies=[Depends(JWTBearer(type='teacher'))])

BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def get_teacher_context(request: Request) -> dict:
    """Returns template context with teacher info from JWT."""
    token = request.cookies.get('token')
    decoded = await decode_jwt(token)
    is_main = decoded['teacher'] == 'Main'
    return {
        'request': request,
        'first_name': 'Sardorbek' if is_main else 'Sevara',
        'last_name': 'Abdulazizov' if is_main else 'Tolipjonova',
        'letters': 'SA' if is_main else 'ST',
        'type': 'Main' if is_main else 'Support',
    }


@router.get('/dashboard', status_code=status.HTTP_200_OK)
async def teacher_dashboard(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/dashboard.html", ctx)


@router.get('/weeks', status_code=status.HTTP_200_OK)
async def weeks(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/weeks.html", ctx)


@router.get('/exercises', status_code=status.HTTP_200_OK)
async def get_exercises_page(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/books.html", ctx)


@router.get('/exercise', status_code=status.HTTP_200_OK)
async def exercise(request: Request, id: UUID = Query(...)):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/exercise.html", ctx)


@router.get('/vocabularies', status_code=status.HTTP_200_OK)
async def get_vocabularies_page(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/vocabularies.html", ctx)


@router.get('/add-separately-choose-the-correct-alternative', status_code=status.HTTP_200_OK)
async def add_separately_choose_correct_alt(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/separately_choose_the_correct_alternative.html", ctx)


@router.get('/add-choose-the-correct-alternative', status_code=status.HTTP_200_OK)
async def add_choose_correct_alt(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/choose_the_correct_alternative.html", ctx)


@router.get('/add-fill-the-gap', status_code=status.HTTP_200_OK)
async def add_fill_the_gap(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/fill_the_gap.html", ctx)


@router.get('/add-separately-fill-the-gap', status_code=status.HTTP_200_OK)
async def add_separately_fill_the_gap(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/separately_fill_the_gap.html", ctx)


@router.get('/add-matching', status_code=status.HTTP_200_OK)
async def add_matching(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/matching.html", ctx)


@router.get('/add-word-order', status_code=status.HTTP_200_OK)
async def add_word_order(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/word_order.html", ctx)


@router.get('/add-complete-the-sentences', status_code=status.HTTP_200_OK)
async def add_complete_sentences(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/complete_the_sentences.html", ctx)


@router.get('/add-separately-complete-the-sentences', status_code=status.HTTP_200_OK)
async def add_separately_complete_sentences(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/separately_complete_the_sentences.html", ctx)


@router.get('/add-rewrite-the-sentences', status_code=status.HTTP_200_OK)
async def add_rewrite_sentences(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/rewrite_the_sentences.html", ctx)


@router.get('/separately-choose-the-correct-alternative', status_code=status.HTTP_200_OK)
async def separately_choose_correct_alt(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/choose_the_correct_alternative.html", ctx)


@router.get('/get-murphy-books', status_code=status.HTTP_200_OK)
async def get_murphy_books(db: db_dependency):
    books = db.query(BooksModel).all()
    return {'success': True, 'books': books}


@router.get("/get-book", status_code=status.HTTP_200_OK)
async def get_book(db: db_dependency, book_id: UUID = Query(...)):
    book = (
        db.query(BooksModel)
        .options(
            selectinload(BooksModel.units)
            .selectinload(UnitsModel.exercises),
            selectinload(BooksModel.ielts_tests)
            .selectinload(IELTSTestsModel.sections)
        )
        .filter(BooksModel.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for unit in book.units:
        if book.level == "Upper-Intermediate":
            unit.ielts_exercises = []
        else:
            unit.exercises = []

    return {"success": True, "book": book}


@router.post('/add-murphy-book', status_code=status.HTTP_201_CREATED)
async def add_murphy_book(request: Request, db: db_dependency):
    json = await request.json()
    db.add(BooksModel(book_name=json['name'], level=json['level']))
    db.commit()
    return {'success': True}


@router.post('/add-book-unit', status_code=status.HTTP_201_CREATED)
async def add_book_unit(request: Request, db: db_dependency):
    json = await request.json()
    unit = ''
    if json['level'] == 'Upper-Intermediate':
        unit = UnitsModel(
            book_id=json['book_id'],
            unit_number=json['unit']
        )
    else:
        unit = IELTSTestsModel(
            book_id=json['book_id'],
            test_number=json['unit']
        )
    db.add(unit)
    db.commit()
    return {'success': True}


@router.post('/add-exercise', status_code=status.HTTP_201_CREATED)
async def add_exercise(data: AddExerciseSchema, db: db_dependency):
    exercise = ExercisesModel(
        unit_id=data.unit_id,
        exercise_type=data.type,
        condition=data.condition,
        exercise_number=data.exercise_number,
    )
    db.add(exercise)
    db.flush()
    db.commit()
    return {'success': True, 'exercise_id': exercise.id}


@router.get('/get-exercise', status_code=status.HTTP_200_OK)
async def get_exercise(db: db_dependency, id: UUID = Query(...)):
    exercise = (
        db.query(ExercisesModel)
        .filter(ExercisesModel.id == id)
        .options(selectinload(ExercisesModel.questions))
        .first()
    )
    return {'success': True, 'exercise': exercise}


@router.post('/add-question', status_code=status.HTTP_201_CREATED)
async def add_question(data: AddExerciseQuestionSchema, db: db_dependency):
    db.add(ExerciseQuestionsModel(exercise_id=data.exercise_id, field=data.field))
    db.commit()
    return {'success': True}


@router.get('/essential-books', status_code=status.HTTP_200_OK)
async def get_essential_books(db: db_dependency):
    books = db.query(EssentialBooksModel).all()
    return {'success': True, 'books': books}


@router.get('/get-essential-book', status_code=status.HTTP_200_OK)
async def get_essential_book(db: db_dependency, book_id: UUID = Query(...)):
    book = (
        db.query(EssentialBooksModel)
        .filter(EssentialBooksModel.id == book_id)
        .options(
            selectinload(EssentialBooksModel.units)
            .selectinload(EssentialUnitsModel.words)
        )
        .first()
    )
    return {'success': True, 'book': book}


@router.post('/add-essential-book', status_code=status.HTTP_201_CREATED)
async def add_essential_book(request: Request, db: db_dependency):
    json = await request.json()
    db.add(EssentialBooksModel(book_number=json['number']))
    db.commit()
    return {'success': True}


@router.post('/add-essential-unit', status_code=status.HTTP_201_CREATED)
async def add_essential_unit(data: AddEssentialUnitSchema, db: db_dependency):
    db.add(EssentialUnitsModel(book_id=data.book_id, unit_number=data.unit_number))
    db.commit()
    return {'success': True}


@router.post('/add-word', status_code=status.HTTP_201_CREATED)
async def add_word(data: AddWordSchema, db: db_dependency):
    db.add(EssentialWordsModel(
        word=data.word,
        meaning=data.meaning,
        translation_uz=data.translation_uz,
        translation_ru=data.translation_ru,
        unit_id=data.unit_id,
        book_id=data.book_id,
    ))
    db.commit()
    return {'success': True}


@router.get('/level-weeks', status_code=status.HTTP_200_OK)
async def get_level_weeks(db: db_dependency, level: str = Query(...)):
    weeks = db.query(WeeksModel).filter(WeeksModel.level == level).order_by(WeeksModel.week_number).all()
    return {'success': True, 'weeks': weeks}


@router.get('/get-clear-groups', status_code=status.HTTP_200_OK)
async def get_clear_groups(db: db_dependency, days: DaysEnum = Query(...)):
    groups = db.query(GroupsModel).filter(GroupsModel.group_days == days.value).all()
    return {'success': True, 'groups': groups}


@router.get('/get-group-results', status_code=status.HTTP_200_OK)
async def get_group_students(month: str, db: db_dependency, id: UUID = Query(...)):
    # 1. Group + students — 1 query
    group = (
        db.query(GroupsModel)
        .options(selectinload(GroupsModel.students))
        .filter(GroupsModel.id == id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # 2. Date range
    start_date = datetime.strptime(month, '%Y-%m')
    now = datetime.now()
    end_date = (
        datetime(start_date.year + 1, 1, 1)
        if start_date.month == 12
        else datetime(start_date.year, start_date.month + 1, 1)
    )
    effective_end_date = min(end_date, now)

    # 3. Week schedules — 2 queries
    week_schedule = db.query(WeekScheduleModel).filter(
        WeekScheduleModel.group_id == id,
        WeekScheduleModel.lesson_date >= start_date,
        WeekScheduleModel.lesson_date < end_date,
    ).all()

    available_schedule = db.query(WeekScheduleModel).filter(
        WeekScheduleModel.group_id == id,
        WeekScheduleModel.lesson_date >= start_date,
        WeekScheduleModel.lesson_date <= effective_end_date,
    ).all()

    if not available_schedule:
        return {'success': True, 'students': [], 'schedule': week_schedule}

    # 4. All weeks — 1 query
    week_numbers = [ws.week_number for ws in available_schedule]
    weeks_list = db.query(WeeksModel).filter(WeeksModel.week_number.in_(week_numbers)).all()
    weeks_dict = {w.week_number: w for w in weeks_list}

    # 5. All Murphy units + exercises + questions — 1 query
    murphy_filters = [
        and_(
            UnitsModel.book_id == w.book,
            UnitsModel.unit_number >= w.book_from_unit,
            UnitsModel.unit_number <= w.book_to_unit,
        )
        for w in weeks_list
    ]
    murphy_units = (
        db.query(UnitsModel)
        .options(
            selectinload(UnitsModel.exercises)
            .selectinload(ExercisesModel.questions)
        )
        .filter(or_(*murphy_filters))
        .all()
    ) if murphy_filters else []

    # 6. All Essential units + words — 1 query
    essential_filters = [
        and_(
            EssentialUnitsModel.book_id == w.essential_book,
            EssentialUnitsModel.unit_number >= w.essential_from_unit,
            EssentialUnitsModel.unit_number <= w.essential_to_unit,
        )
        for w in weeks_list
    ]
    vocabularies = (
        db.query(EssentialUnitsModel)
        .options(selectinload(EssentialUnitsModel.words))
        .filter(or_(*essential_filters))
        .all()
    ) if essential_filters else []

    student_ids = [s.id for s in group.students]
    exercise_ids = [e.id for mu in murphy_units for e in mu.exercises]
    vocab_ids = [v.id for v in vocabularies]

    ex_results = (
        db.query(
            StudentResultsModel.student_id,
            StudentResultsModel.exercise_id,
            func.count(StudentResultsModel.id).label('cnt'),
        )
        .filter(
            StudentResultsModel.student_id.in_(student_ids),
            StudentResultsModel.exercise_id.in_(exercise_ids),
            StudentResultsModel.passed == True,
        )
        .group_by(StudentResultsModel.student_id, StudentResultsModel.exercise_id)
        .all()
    ) if exercise_ids else []

    voc_results = (
        db.query(
            StudentResultsModel.student_id,
            StudentResultsModel.vocabulary_unit_id,
            func.count(StudentResultsModel.id).label('cnt'),
        )
        .filter(
            StudentResultsModel.student_id.in_(student_ids),
            StudentResultsModel.vocabulary_unit_id.in_(vocab_ids),
            StudentResultsModel.passed == True,
        )
        .group_by(StudentResultsModel.student_id, StudentResultsModel.vocabulary_unit_id)
        .all()
    ) if vocab_ids else []

    # 8. Fast lookup dicts
    ex_lookup = {(r.student_id, r.exercise_id): r.cnt for r in ex_results}
    voc_lookup = {(r.student_id, r.vocabulary_unit_id): r.cnt for r in voc_results}

    murphy_by_week = {}
    vocab_by_week = {}
    for w in weeks_list:
        murphy_by_week[w.id] = [
            mu for mu in murphy_units
            if mu.book_id == w.book
               and w.book_from_unit <= mu.unit_number <= w.book_to_unit
        ]
        vocab_by_week[w.id] = [
            v for v in vocabularies
            if v.book_id == w.essential_book
               and w.essential_from_unit <= v.unit_number <= w.essential_to_unit
        ]

    students_copy = []
    for student in group.students:
        s = student.__dict__.copy()
        s.pop('_sa_instance_state', None)
        s['progress'] = []

        for ws in available_schedule:
            week = weeks_dict.get(ws.week_number)
            if not week:
                continue

            q_count = p_count = 0

            for mu in murphy_by_week.get(week.id, []):
                for ex in mu.exercises:
                    q_count += len(ex.questions)
                    p_count += ex_lookup.get((student.id, ex.id), 0)

            for vocab in vocab_by_week.get(week.id, []):
                q_count += len(vocab.words)
                p_count += voc_lookup.get((student.id, vocab.id), 0)

            s['progress'].append({
                'week_id': week.id,
                'percent': round((p_count / q_count) * 100) if q_count else 0,
            })

        students_copy.append(s)

    return {'success': True, 'students': students_copy, 'schedule': week_schedule}


@router.post('/add-week', status_code=status.HTTP_200_OK)
async def add_week(data: AddWeekSchema, db: db_dependency):
    db.add(WeeksModel(
        week_number=data.week_number,
        level=data.level,
        essential_book=data.essential_book,
        essential_from_unit=data.essential_from_unit,
        essential_to_unit=data.essential_to_unit,
        book=data.murphy_book,
        book_from_unit=data.murphy_from_unit,
        book_to_unit=data.murphy_to_unit,
        keys=data.keys,
        week_topic=data.week_topic,
    ))
    db.commit()
    return {'success': True}


@router.get('/get-results', status_code=status.HTTP_200_OK)
async def get_results(
        db: db_dependency,
        student_id: UUID = Query(...),
        week_id: UUID = Query(...),
        type: str = Query(...),
):
    # 1. Get the week
    week = db.query(WeeksModel).filter(WeeksModel.id == week_id).first()
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")

    # 2. Get the student
    student = db.query(StudentsModel).filter(StudentsModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if type == 'Vocab':
        vocab_units = (
            db.query(EssentialUnitsModel)
            .options(selectinload(EssentialUnitsModel.words))
            .filter(
                EssentialUnitsModel.book_id == week.essential_book,
                EssentialUnitsModel.unit_number >= week.essential_from_unit,
                EssentialUnitsModel.unit_number <= week.essential_to_unit,
            )
            .all()
        )

        submitted = db.query(StudentResultsModel).filter(
            StudentResultsModel.student_id == student_id,
            StudentResultsModel.week_id == week_id,
            StudentResultsModel.type == 'Vocab',
        ).all()

        result_by_word = {r.vocabulary_id: r for r in submitted}

        full_results = []
        for unit in vocab_units:
            for word in unit.words:
                full_results.append({
                    'word': word,
                    'unit': unit,
                    'result': result_by_word.get(word.id, None),
                    'submitted': word.id in result_by_word,
                })

        return {
            'ok': True,
            'type': 'Vocab',
            'student': student,
            'week': week,
            'results': full_results,
            'total': len(full_results),
            'submitted_count': len(submitted),
            'missing_count': len(full_results) - len(submitted),
        }

    elif type == 'Exercise':
        print(week.book)
        book = db.query(BooksModel).filter(BooksModel.id == week.book).first()
        print(book)
        is_ielts = book.level == LevelsEnum.IELTS

        if is_ielts:
            units = (
                db.query(IELTSTestsModel)
                .options(
                    selectinload(IELTSTestsModel.sections)
                    .selectinload(IELTSSectionsModel.questions)
                )
                .filter(
                    IELTSTestsModel.book_id == week.book,
                    IELTSTestsModel.test_number >= week.book_from_unit,
                    IELTSTestsModel.test_number <= week.book_to_unit,
                )
                .all()
            )
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

        submitted = db.query(StudentResultsModel).filter(
            StudentResultsModel.student_id == student_id,
            StudentResultsModel.week_id == week_id,
            StudentResultsModel.type == 'Exercise',
        ).all()

        # ✅ Key by ielts_section_id for IELTS, exercise_id for Murphy
        if is_ielts:
            result_by_exercise = {r.ielts_section_id: r for r in submitted}
        else:
            result_by_exercise = {r.exercise_id: r for r in submitted}

        full_results = []

        if is_ielts:
            for test in units:
                for section in test.sections:  # ✅ IELTSTestsModel -> .sections
                    full_results.append({
                        'exercise': section,
                        'unit': test,
                        'questions': section.questions,
                        'result': result_by_exercise.get(section.id, None),
                        'submitted': section.id in result_by_exercise,
                    })
        else:
            for unit in units:
                for exercise in unit.exercises:  # ✅ UnitsModel -> .exercises
                    full_results.append({
                        'exercise': exercise,
                        'unit': unit,
                        'questions': exercise.questions,
                        'result': result_by_exercise.get(exercise.id, None),
                        'submitted': exercise.id in result_by_exercise,
                    })

        return {
            'ok': True,
            'type': 'Exercise',
            'is_ielts': is_ielts,
            'student': student,
            'week': week,
            'results': full_results,
            'total': len(full_results),
            'submitted_count': len(submitted),
            'missing_count': len(full_results) - len(submitted),
        }

    else:
        raise HTTPException(status_code=400, detail="type must be 'Vocab' or 'Exercise'")


@router.post('/upload', status_code=status.HTTP_201_CREATED)
async def file_upload(db: db_dependency, file: UploadFile = File()):
    ext = Path(file.filename).suffix
    unique_name = f"{uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_name

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_model = FilesModel(
            file_path=str(file_path)
        )

        db.add(file_model)
        db.commit()
        db.refresh(file_model)

        return {
            "ok": True,
            "id": file_model.id,
            "filename": unique_name
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}"
        )
    finally:
        await file.close()


@router.get('/add-dictation-test', status_code=status.HTTP_200_OK)
async def add_ielts_listening_task(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/add_dictation_listening.html", ctx)


@router.post('/add-dictation', status_code=201)
async def add_ielts_listening(
        data: AddIELTSListeningSchema,
        background_tasks: BackgroundTasks,
        db: db_dependency
):
    audio = db.query(FilesModel).filter(
        FilesModel.id == data.audio_id
    ).first()

    if not audio:
        raise HTTPException(404, 'Audio not found')

    dictation = IELTSSectionsModel(
        test_id=data.unit_id,
        module=IELTSModule.DICTATION,
        section_number=data.test_number,
        audio_file_id=audio.id
    )

    db.add(dictation)
    db.commit()
    db.refresh(dictation)

    background_tasks.add_task(
        get_transcribe_with_ai,
        audio.file_path, dictation.id
    )

    return {
        "ok": True,
        "message": "Audio added. Ai is working on.",
        "id": dictation.id
    }

@router.get('/add-ielts-reading-test', status_code=status.HTTP_200_OK)
async def add_ielts_reading(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/add_ielts_reading.html", ctx)\

@router.post('/add-reading-part1', status_code=status.HTTP_201_CREATED)
async def add_ielts_reading(data: AddIELTSReadingSchema, db: db_dependency):
    reading = IELTSSectionsModel(
        test_id=data.unit_id,
        module=IELTSModule.READING,
        section_number=data.test_number,
        passage_text=data.passage,
        status='ready'
    )
    db.add(reading)
    counter = 1
    for q in data.questions:
        question = IELTSQuestionsModel(
            section_id=reading.id,
            question_number=counter,
            question_type=q['type'],
            question_data=q
        )
        db.add(question)
    db.commit()
    db.close()
    return {'ok': True}

@router.get('/add-ielts-listening-fill-the-gap', status_code=status.HTTP_200_OK)
async def add_ielts_reading(request: Request):
    ctx = await get_teacher_context(request)
    return templates.TemplateResponse("teachers/add_ielts_listening_fill_the_gaps.html", ctx)
