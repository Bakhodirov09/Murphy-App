import json
from fastapi import FastAPI, status, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from httpx import AsyncClient
from pathlib import Path
from web.data import LOGIN_REQUEST_HEX_KEY, LOGIN_INTER_URL, LOGIN_RESPONSE_HEX_KEY, tashkent
from web.general import create_token, templates, decode_jwt, db_dependency, send_otp_for_teacher
from web.models import TeachersModel, OTPCodesModel
from web.schemas import LoginRequest, UpdatePasswordSchema, SendOTPSchema
from web.header import make_header, encrypt_aes_base64, decrypt_aes_base64
from web.routers.student_routers import router as student_router
from web.routers.teacher_routers import router as teacher_router

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent


@app.middleware("http")
async def add_ngrok_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response


@app.get('/')
async def root(request: Request):
    token = request.cookies.get('token')
    if not token:
        return RedirectResponse(url=f'/login?{request.query_params}')
    try:
        decoded_token = await decode_jwt(token)
        if decoded_token['type'] == 'student':
            return RedirectResponse(url='/student/dashboard')
        return RedirectResponse(url='/teacher/dashboard')
    except Exception as e:
        response = RedirectResponse(url=f'/login?{request.query_params}')
        response.delete_cookie('token')
        return response


@app.get('/login', status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse(request, 'login.html')


@app.post('/login', status_code=status.HTTP_200_OK)
async def login(request: Request, data: LoginRequest, db: db_dependency, chat_id: int = Query(...)):
    phone_clean = data.login.replace(" ", "").replace("(", "").replace(")", "").replace("-", "").replace("+", "")
    teacher = db.query(TeachersModel).filter(
        TeachersModel.phone_number == phone_clean
    ).first()
    if teacher:
        if teacher.password == data.password:
            response = {
                'success': True,
                'token': await create_token({'teacher': teacher.type, 'type': 'teacher'}),
                'teacher': {
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'avatar_url': teacher.avatar_url
                },
                'role': teacher.type
            }
            return response
    else:
        body = {'project': 'lms-v2', 'action': 'client_auth_universal_login',
                'body': {'login': data.login, 'password': data.password}}
        encrypted = {'a': await encrypt_aes_base64(body, LOGIN_REQUEST_HEX_KEY)}
        encrypted_body = json.dumps(encrypted, separators=(',', ':'))
        header = await make_header(encrypted_body, request.headers.get('User-Agent'))
        async with AsyncClient(http2=True, headers=header) as client:
            response = await client.post(url=LOGIN_INTER_URL, content=encrypted_body)
            if response.status_code == 200:
                r_json = await decrypt_aes_base64(response.json()['a'], LOGIN_RESPONSE_HEX_KEY)
                if r_json['user']['group']['level_label'] in ['Upper-Intermediate', 'IELTS']:
                    response = {
                        'success': False,
                        'user': {
                            'first_name': r_json['user']['first_name'],
                            'last_name': r_json['user']['last_name'],
                            'avatar_url': r_json['user']['avatar_url'],
                            'group': r_json['user']['group']['name'],
                            'level': r_json['user']['group']['level_label'],
                            'sub': r_json['user']['group']['sub_label'],
                            'chat_id': chat_id
                        }
                    }
                    if r_json['user']['teacher']['first_name'] == "Sardorbek" \
                            and r_json['user']['teacher']['last_name'] == "Abdulazizov":
                        response['success'] = True
                        response['token'] = await create_token({'user': response['user'], 'type': 'student'})
                        response['type'] = 'student'
                        response['chat_id'] = request.query_params.get('chat_id')
                        resp = JSONResponse(response)
                        resp.set_cookie(
                            key='token',
                            value=response['token'],
                            httponly=True,
                            max_age=60 * 60 * 24 * 15,
                            path='/',
                            samesite='lax'
                        )
                        return resp
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'success': False, 'level': False})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Login or password is incorrect')



@app.get('/success', status_code=200)
async def success_audio():
    return FileResponse(
        path=f'{BASE_DIR}/assets/audios/success.mp3',
        media_type='audio/mpeg'
    )


@app.get('/incorrect', status_code=status.HTTP_200_OK)
async def success_audio():
    return FileResponse(
        path=f'{BASE_DIR}/assets/audios/wrong.mp3',
        media_type='audio/mpeg'
    )


@app.get('/task', status_code=status.HTTP_200_OK)
async def task_image():
    return FileResponse(
        path=f'{BASE_DIR}/assets/images/task.png',
        media_type='image/png'
    )


@app.get('/bg1', status_code=status.HTTP_200_OK)
async def task_image():
    return FileResponse(
        path=f'{BASE_DIR}/assets/images/bg1.png',
        media_type='image/png'
    )


@app.get('/bg3', status_code=status.HTTP_200_OK)
async def task_image():
    return FileResponse(
        path=f'{BASE_DIR}/assets/images/bg3.png',
        media_type='image/png'
    )

@app.post('/teacher/login/send-otp', status_code=status.HTTP_200_OK)
async def request_to_update_password(data: SendOTPSchema, db: db_dependency):
    phone_clean = data.phone_number.replace(" ", "").replace("(", "").replace(")", "").replace("-", "").replace("+", "")
    teacher = db.query(TeachersModel).filter(
        TeachersModel.phone_number == phone_clean
    ).first()
    if teacher:
        sent = await send_otp_for_teacher(phone_clean)
        if sent['ok']:
            code = OTPCodesModel(
                code=sent['code'],
                phone_number=phone_clean
            )
            db.add(code)
            db.commit()
            return {'ok': True, 'message': 'OTP Sent'}
        return HTTPException(detail={'ok': False, 'message': "OTP couldn't send"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    raise HTTPException(detail={'ok': False}, status_code=status.HTTP_404_NOT_FOUND)

@app.post('/teacher/login/update-password', status_code=status.HTTP_200_OK)
async def update_password(data: UpdatePasswordSchema, db: db_dependency):
    phone_clean = data.phone_number.replace(" ", "").replace("(", "").replace(")", "").replace("-", "").replace("+", "")
    code = db.query(OTPCodesModel).filter(
        OTPCodesModel.code == int(data.otp_code),
    ).first()
    if not code:
        raise HTTPException(detail={'ok': False, 'message': 'OTP Code not found'}, status_code=status.HTTP_404_NOT_FOUND)

    teacher = db.query(TeachersModel).filter(
        TeachersModel.phone_number == phone_clean
    ).first()
    if not teacher:
        db.delete(code)
        db.commit()
        raise HTTPException(detail={'ok': False, 'message': 'Teacher not found'}, status_code=status.HTTP_404_NOT_FOUND)
    teacher.password = data.new_password
    db.commit()
    return {'ok': True, 'message': 'Updated successfully'}


app.include_router(student_router, prefix='/student', tags=['Student Routers'])
app.include_router(teacher_router, prefix='/teacher', tags=['Teacher Routers'])
