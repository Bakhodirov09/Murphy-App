import json
from fastapi import FastAPI, status, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from httpx import AsyncClient, Client
from starlette.templating import Jinja2Templates

from web.data import LOGIN_REQUEST_HEX_KEY, LOGIN_INTER_URL, LOGIN_RESPONSE_HEX_KEY
from web.general import create_token, templates, decode_jwt
from web.schemas import LoginRequest
from web.header import make_header, encrypt_aes_base64, decrypt_aes_base64
from web.routers.student_routers import router as student_router
from web.routers.teacher_routers import router as teacher_router

app = FastAPI()

# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/')
async def root(request: Request):
    token = request.cookies.get('token')
    if not token:
        return RedirectResponse(url=f'/login?{request.query_params}')
    decoded_token = await decode_jwt(token)
    if decoded_token['type'] == 'student':
        return RedirectResponse(url='/student/dashboard')
    return RedirectResponse(url='/teacher/dashboard')

@app.get('/login', status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse(request, 'login.html')

@app.post('/login', status_code=status.HTTP_200_OK)
async def login(request: Request, data: LoginRequest, chat_id: int = Query(...)):
    if not data.password.isdigit():
        body = {'project': 'lms-v2', 'action': 'client_auth_universal_login', 'body': {'login': data.login, 'password': data.password}}
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
                    if r_json['user']['teacher']['id'] == 73617:
                        response['success'] = True
                        response['token'] = await create_token({'user': response['user'], 'type': 'student'})
                        response['type'] = 'student'
                        response['chat_id'] = request.query_params.get('chat_id')
                        return response
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'success': False, 'level': False})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Login or password is incorrect')
    else:
        teacher_numbers = ['+998 (94) 930-62-22', '+998 (90) 859-79-39']
        if data.login in teacher_numbers:
            if data.login == teacher_numbers[0] and data.password == "967402800":
                return {
                    'success': True,
                    'token': await create_token({'teacher': 'Main', 'type': 'teacher'}),
                    'teacher': {
                        'first_name': 'Sardorbek',
                        'last_name': 'Abdulazizov',
                        'avatar_url': 'https://file-server-5x5bbmyc8vmh94yt.inter-nation.uz/7/2HE_pDQBzQyg3cVBIvyxu2ia4Q5YMu1a.jpg'
                    },
                    'role': 'Main'
                }
            elif data.login == teacher_numbers[1] and data.password == '1149620400':
                return {
                    'success': True,
                    'token': await create_token({'teacher': 'Support', 'type': 'teacher'}),
                    'teacher': {
                        'first_name': 'Sevara',
                        'last_name': 'Tolipjonova',
                        'avatar_url': 'https://file-server-5x5bbmyc8vmh94yt.inter-nation.uz/10/vP9Ql_GWZ5wmcg7SjAMtivpYWtdTc--w.jpg'
                    },
                    'role': 'Support'
                }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Login or password is incorrect')

@app.get('/success', status_code=status.HTTP_200_OK)
async def success_audio():
    async with AsyncClient() as client:
        response = await client.get('https://web-student.inter-nation.uz/audio/success.mp3')

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "audio/mpeg"
    }

    return Response(content=response.content, status_code=200, headers=headers)

@app.get('/incorrect', status_code=status.HTTP_200_OK)
async def success_audio():
    async with AsyncClient() as client:
        response = await client.get('https://web-student.inter-nation.uz/audio/wrong.mp3')

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "audio/mpeg"
    }

    return Response(content=response.content, status_code=200, headers=headers)

@app.get('/task', status_code=status.HTTP_200_OK)
async def task_image():
    async with AsyncClient() as client:
        response = await client.get('https://web-student.inter-nation.uz/_next/image?url=%2Fimages%2Flesson%2Fexercise%2Fdefault.png&w=96&q=75')

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "image/png"
    }

    return Response(content=response.content, status_code=200, headers=headers)

@app.get('/bg1', status_code=status.HTTP_200_OK)
async def task_image():
    async with AsyncClient() as client:
        response = await client.get('https://web-student.inter-nation.uz/images/lesson/bg1.png')

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "image/png"
    }

    return Response(content=response.content, status_code=200, headers=headers)

@app.get('/bg3', status_code=status.HTTP_200_OK)
async def task_image():
    async with AsyncClient() as client:
        response = await client.get('https://web-student.inter-nation.uz/images/lesson/bg3.png')

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "image/png"
    }

    return Response(content=response.content, status_code=200, headers=headers)

app.include_router(student_router, prefix='/student', tags=['Student Routers'])
app.include_router(teacher_router, prefix='/teacher')