import difflib
import os
import random
import re

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
from web.models import IELTSSectionsModel

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


# def process_dictation_script_with_ai(dictation_id: str, script):
#     db = SessionLocal()
#     listening = db.query(IELTSSectionsModel).get(dictation_id)
#     if not listening:
#         return
#     try:
#
#         prompt = f"""
# You are an expert English teacher and IELTS listening grader.
# I will give you a listening dictation script.
# Your task:
# 1. Remove all unnecessary words, stopwords (the, a, an, is, are, was, were, to, of, in, on, at, for, with, and, etc.), filler words, and punctuation.
# 2. Keep only the important words that a student have to write down.
# 3. Return JSON with two keys:
#    - "canonical_text": the cleaned text the student have to write.
#    - "removed_words": list of words or characters you removed.
#
# Listening script:
# \"\"\"
# {script}
# \"\"\"
# """
#
#         response = openai_client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )
#
#         cleaned = response.choices[0].message.json
#
#         listening.script = script
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

def get_transcribe_with_ai(file, dictation_id: str):
    db = SessionLocal()
    try:
        listening = db.query(IELTSSectionsModel).filter(
            IELTSSectionsModel.id == dictation_id
        ).first()

        if not listening:
            return {'ok': False, 'error': 'Section not found'}

        with open(file, "rb") as f:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json"
            )

        segments_oai = response.segments
        segments = [{'text': s.text, 'start': s.start, 'end': s.end} for s in segments_oai]

        listening.transcript = response.text
        listening.segments = segments
        listening.status = 'ready'

        db.commit()

        return True

    except Exception as e:
        db.rollback()
        with open('errors.txt', 'a') as writer:
            writer.write(f'|{e}_whisper-1')
        return {'ok': False, 'error': str(e)}
    finally:
        db.close()


def send_otp_for_teacher(phone_number):
    code = ''
    for _ in range(6):
        code += str(random.randint(0, 9))
    response_data = sms.send_message(
        {
            'from': 'Murphy-App',
            'to': phone_number,
            'text': f'Your code to update your password on Murphy-App: {code}'
        }
    )
    if response_data["messages"][0]["status"] == "0":
        return {'ok': True, 'code': code, 'data': response_data}
    return {'ok': False}

print(send_otp_for_teacher('998949306222'))

def clean_text(text: str):
    text = text.lower()
    text = text.replace('-', ' ')
    text = re.sub(r"[^\w\s']", "", text)
    text = re.sub(r'\s+', ' ', text)
    return text.split()

def normalize_word(word: str) -> str:
    """hard working -> hardworking, hard-working -> hardworking"""
    return word.replace('-', '').replace(' ', '')

def words_match(w1: str, w2: str) -> bool:
    """hardworking == hard working == hard-working"""
    return normalize_word(w1) == normalize_word(w2)

def check_student_answer(student_text, correct_words, segments):
    student_words = clean_text(student_text)

    correct_norm = [normalize_word(w) for w in correct_words]
    student_norm = [normalize_word(w) for w in student_words]

    matcher = difflib.SequenceMatcher(None, correct_norm, student_norm)

    word_to_segment = []
    for seg in segments:
        seg_words = clean_text(seg['text'])
        for _ in seg_words:
            word_to_segment.append(seg)

    seg_errors = {}

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag not in ("delete", "replace"):
            continue

        for i in range(i1, i2):
            seg = word_to_segment[i] if i < len(word_to_segment) else None
            if not seg:
                continue

            if tag == "replace":
                student_chunk = " ".join(student_words[j1:j2])
                if normalize_word(correct_words[i]) == normalize_word(student_chunk):
                    continue

            key = seg['start']
            if key not in seg_errors:
                seg_errors[key] = {
                    "sentence": seg['text'].strip(),
                    "segment_start": seg['start'],
                    "segment_end": seg['end'],
                    "wrote": "",
                }

    seg_student_words = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        for i in range(i1, min(i2, len(word_to_segment))):
            seg = word_to_segment[i]
            key = seg['start']
            if tag == "equal":
                idx = j1 + (i - i1)
                if idx < len(student_words):
                    seg_student_words.setdefault(key, []).append(student_words[idx])
            elif tag in ("replace", "insert"):
                if i == i1:
                    for jj in range(j1, j2):
                        seg_student_words.setdefault(key, []).append(student_words[jj])

    for key, err in seg_errors.items():
        err["wrote"] = " ".join(seg_student_words.get(key, []))

    return [err for err in seg_errors.values()]
