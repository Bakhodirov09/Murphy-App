import json
from fastapi import APIRouter, Request, HTTPException
from fastapi import status
from fastapi import Depends
from httpx import AsyncClient
from web.general import db_dependency, create_token, decode_jwt, JWTBearer
from web.header import make_header, decrypt_aes_base64, encrypt_aes_base64
from web.schemas import LoginRequest, GroupDaysRequest
from web.data import LOGIN_INTER_URL, LOGIN_REQUEST_HEX_KEY, LOGIN_RESPONSE_HEX_KEY
from web.models import GroupsModel, StudentsModel

router = APIRouter()

@router.post('/ok', status_code=status.HTTP_201_CREATED)
async def ok(request: Request, db: db_dependency, token: str = Depends(JWTBearer())):
    decoded_token = await decode_jwt(token)
    student = StudentsModel(
        first_name=decoded_token['user']['first_name'],
        last_name=decoded_token['user']['last_name'],
    )
    db.add(student)
    group = db.query(GroupsModel).filter(GroupsModel.group_name == decoded_token['user']['group']).first()
    db.flush()
    db.refresh(student)
    new_token = await create_token({'student_id': str(student.id)})
    if group:
        student.group_id = group.id
        return {
            'new_token': new_token
        }
    db.commit()
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'message': 'Group not found', 'new_token': new_token, 'group': decoded_token['user']['group']})

@router.post('/create-group', status_code=status.HTTP_201_CREATED)
async def create_group(data: GroupDaysRequest, db: db_dependency, token: str = Depends(JWTBearer())):
    decoded_token = await decode_jwt(token)
    new_group = GroupsModel(
        group_name=data.group,
        group_days='Odd Dates' if data.days == 0 else 'Even Days'
    )
    db.add(new_group)
    db.flush()
    db.refresh(new_group)
    student = db.query(StudentsModel).filter(StudentsModel.id == decoded_token['student_id']).first()
    student.group_id = new_group.id
    db.commit()
    return {
        'ok': True
    }
