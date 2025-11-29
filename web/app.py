import json
from fastapi import FastAPI, status, Request, HTTPException
from fastapi.responses import HTMLResponse
from httpx import AsyncClient
from web.data import LOGIN_REQUEST_HEX_KEY, LOGIN_INTER_URL, LOGIN_RESPONSE_HEX_KEY
from web.general import create_token
from web.schemas import LoginRequest
from web.header import make_header, encrypt_aes_base64, decrypt_aes_base64
from web.routes.student_routes import router

app = FastAPI()

@app.get('/login', status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def get_login():
    return HTMLResponse(content='index.html')

@app.post('/login', status_code=status.HTTP_200_OK)
async def login(request: Request, data: LoginRequest):
    body = {'project': 'lms-v2', 'action': 'client_auth_universal_login', 'body': {'login': data.login, 'password': data.password}}
    encrypted = {'a': await encrypt_aes_base64(body, LOGIN_REQUEST_HEX_KEY)}
    encrypted_body = json.dumps(encrypted, separators=(',', ':'))
    header = await make_header(encrypted_body, request.headers.get('User-Agent'))
    async with AsyncClient(http2=True, headers=header) as client:
        response = await client.post(url=LOGIN_INTER_URL, content=encrypted_body)
        if response.status_code == 200:
            r_json = await decrypt_aes_base64(response.json()['a'], LOGIN_RESPONSE_HEX_KEY)
            if r_json['user']['group']['level_label'] in ['Intermediate', 'Upper-Intermediate', 'IELTS']:
                response = {
                    'success': False,
                    'user': {
                        'first_name': r_json['user']['first_name'],
                        'last_name': r_json['user']['last_name'],
                        'avatar_url': r_json['user']['avatar_url'],
                        'group': r_json['user']['group']['name'],
                        'level': r_json['user']['group']['level_label']
                    }
                }
                if r_json['user']['teacher']['id'] == 73617:
                    response['success'] = True
                    response['token'] = await create_token({'user': response['user'], })
                    return response
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'success': False, 'level': False})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Login or password is incorrect')

app.include_router(router, prefix='/students', tags=['Students'])