from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from uuid import UUID
from web.data import tashkent
from web.general import db_dependency, create_token, decode_jwt, JWTBearer
from web.schemas import GroupDaysRequest
from web.models import GroupsModel, StudentsModel, WeeksModel, WeekScheduleModel, MurphyUnitsModel, EssentialUnitsModel

router = APIRouter(dependencies=[Depends(JWTBearer(type='student'))])


async def get_first_lesson_date(months_ago: int, weekday: int):
    target_month = (datetime.now(tashkent) - relativedelta(months=months_ago)).replace(day=1)
    offset = (weekday - target_month.weekday()) % 7

    return target_month + timedelta(days=offset)

@router.get('/dashboard', status_code=status.HTTP_200_OK)
async def dashboard():
    return {'ok': False, 'message': "Students' dashboard is on the proccess"}

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
        group_days='Odd Days' if data.days == 0 else 'Even Days'
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
    return {'success': True, 'student': student, 'weeks': group_weeks}

@router.get('/get-week', status_code=status.HTTP_200_OK)
async def get_week(request: Request, db: db_dependency, week_id: UUID = Query(...)):
    token = request.cookies.get('token')
    decoded_token = await decode_jwt(token)
    week = db.query(WeeksModel).filter(WeeksModel.id == week_id).first()
    if week:
        murphy_units = db.query(MurphyUnitsModel).filter(
            MurphyUnitsModel.unit_number >= week.murphy_from_unit,
            MurphyUnitsModel.unit_number <= week.murphy_to_unit,
        )
        vocabulary_units = db.query(EssentialUnitsModel).filter(
            EssentialUnitsModel.unit_number >= week.essential_from_unit,
            EssentialUnitsModel.unit_number <= week.essential_to_unit,
        )
        vocabularies = list()
        murphy_exercises = list()
        # for vocabulary in vocabulary_units:
        #     vocabularies.append({'id': vocabulary.id, ''})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
