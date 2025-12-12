from datetime import datetime

from fastapi import APIRouter, Depends, status, Request, Query
from uuid import UUID
from web.general import JWTBearer, db_dependency, decode_jwt
from web.models import GroupsModel, WeeksModel, WeekScheduleModel, EssentialUnitsModel, MurphyUnitsModel, \
    StudentResultsModel
from web.general import templates
from web.schemas import AddWeekSchema

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
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)
    week_schedule = (
        db.query(WeekScheduleModel)
        .filter(
            WeekScheduleModel.group_id == id,
            WeekScheduleModel.lesson_date >= start_date,
            WeekScheduleModel.lesson_date < end_date
        )
        .all()
    )
    students_copy = list()
    for student in students.students:
        student_copy = student.__dict__.copy()
        for week_s in week_schedule:
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
            progress = list()
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
            progress.append({
                'week_id': week.id,
                'percent': int((p_count / q_count) * 100) if q_count != 0 else 0
            })
            student_copy['progress'] = progress
            students_copy.append(student_copy)
    return {'success': True, 'students': students_copy, 'schedule': week_schedule}

@router.post('/add-week', status_code=status.HTTP_200_OK)
async def add_week(data: AddWeekSchema, db: db_dependency):
    week = WeeksModel(
        week_number=data.week_number,
        level=data.level,
        essential_from_unit=data.essential_from_unit,
        essential_to_unit=data.essential_to_unit,
        murphy_from_unit=data.murphy_from_unit,
        murphy_to_unit=data.murphy_to_unit,
        keys=data.keys,
        week_topic=data.week_topic
    )
    db.add(week)
    db.flush()
    db.commit()
    return {'success': True}

@router.get('/exercises', status_code=status.HTTP_200_OK)
async def get_exercises_page(request: Request):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    return templates.TemplateResponse("teachers/exercises.html", {
        "request": request,
        "first_name": 'Sardorbek' if decoded_token['teacher'] == 'Main' else 'Sevara',
        "last_name": 'Abdulazizov' if decoded_token['teacher'] == 'Main' else 'Tolipjonova',
        "letters": 'SA' if decoded_token['teacher'] == 'Main' else 'ST',
        "type": 'Main' if decoded_token['teacher'] == 'Main' else 'Support',
    })

@router.get('/add-question', status_code=status.HTTP_201_CREATED)
async def add_question(data, db: db_dependency):
    pass
