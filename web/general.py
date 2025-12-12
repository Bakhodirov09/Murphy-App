import os
from datetime import datetime
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from fastapi import Request, Depends
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from web.data import SECRET_KEY, ALGORITHM, tashkent
from web.database import SessionLocal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_token(token_data):
    encoded = token_data
    return jwt.encode(encoded, SECRET_KEY, ALGORITHM)

db_dependency = Annotated[Session, Depends(get_db)]

async def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return {}

class JWTBearer(HTTPBearer):
    def __init__(self, cookie_name: str = 'token', auto_error: bool = True, type: str = None):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.cookie_name = cookie_name
        self.type = type

    async def __call__(self, request: Request):
        token = request.cookies.get(self.cookie_name)
        decoded_token = await self.verify_jwt(token)
        if not token:
            raise HTTPException(status_code=403, detail="Token not found")
        if decoded_token[1].get('type') != self.type:
            raise HTTPException(status_code=403, detail="You have no permission.")
        return token

    async def verify_jwt(self, jwt_token: str):

        try:
            payload = await decode_jwt(jwt_token)
        except:
            payload = None

        return [bool(payload), payload] if payload else False