import os
import random

import openai
import vonage
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from fastapi import Request, Depends
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates
from web.data import SECRET_KEY, ALGORITHM, OPENAI_API_KEY, VONAGE_KEY, VONAGE_API_SECRET
from web.database import SessionLocal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
vonage_client = vonage.Client(key=VONAGE_KEY, secret=VONAGE_API_SECRET)
sms = vonage.Sms(vonage_client)


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


# def process_script_with_ai(listening_id: int):
#     db = SessionLocal()
#
#     try:
#         listening = db.query(IELTSMaterialsModel).get(listening_id)
#         if not listening:
#             return
#
#         prompt = f"""
# You are an expert English teacher and IELTS listening grader.
# I will give you a listening script.
# Your task:
# 1. Remove all unnecessary words, stopwords (the, a, an, is, are, was, were, to, of, in, on, at, for, with, and, etc.), filler words, and punctuation.
# 2. Keep only the important words that a student should write down.
# 3. Return JSON with two keys:
#    - "canonical_text": the cleaned text the student should write.
#    - "removed_words": list of words or characters you removed.
#
# Listening script:
# \"\"\"
# {listening.script}
# \"\"\"
# """
#
#         response = openai_client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )
#
#         cleaned = response.choices[0].message.content
#
#         listening.cleaned_script = cleaned['canonical_text']
#         listening.removed_words = cleaned['removed_words']
#         listening.status = "done"
#         db.commit()
#
#     except Exception as e:
#         listening.status = "error"
#         db.commit()
#
#     finally:
#         db.close()


async def send_otp_for_teacher(phone_number):
    code = ''
    for _ in range(6):
        code += str(random.randint(0, 9))
    response_data = sms.send_message(
        {
            'from': 'Murphy-App',
            'to': phone_number,
            'text': f'Your code: {code}'
        }
    )
    if response_data["messages"][0]["status"] == "0":
        return {'ok': True, 'code': code}
    return {'ok': False}
