import base64
import hashlib
import json
import time
import hmac
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from web.data import LOGIN_SECRET_KEY, LOGIN_STATIC_STR, LOGIN_HEADER_HEX_KEY


async def decrypt_aes_base64(encrypted_b64: str, hex_key: str):
    key = bytes.fromhex(hex_key)
    encrypted_bytes = base64.b64decode(encrypted_b64)

    iv = encrypted_bytes[:16]
    ciphertext = encrypted_bytes[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)

    pad_len = decrypted[-1]
    decrypted = decrypted[:-pad_len]

    return json.loads(decrypted.decode("utf-8"))

async def encrypt_aes_base64(plaintext, hex_key: str) -> str:
    key = bytes.fromhex(hex_key)
    iv = get_random_bytes(16)

    plaintext = json.dumps(plaintext, separators=(',', ":"))

    pad_len = 16 - (len(plaintext.encode("utf-8")) % 16)
    padded = plaintext.encode("utf-8") + bytes([pad_len] * pad_len)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(padded)

    encrypted_bytes = iv + ciphertext
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")

    return encrypted_b64

async def make_header(body, user_agent):
    async def make_a():
        t = int(time.time())
        a = {
            'u': None,
            's': hmac.new(LOGIN_SECRET_KEY.encode(), f"{t}{body}{t}{LOGIN_STATIC_STR}{body}".encode(), hashlib.sha256).hexdigest(),
            'h': None,
            't': t,
            'l': 'uz',
            'User-Device': 'Web-Chrome'
        }
        return await encrypt_aes_base64(json.dumps(a, separators=(',', ':')), LOGIN_HEADER_HEX_KEY)
    header = {
        "Host": "login.inter-nation.uz",
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "timeout": "5000",
        "a": await make_a(),
        "Content-Length": str(len(body)),
        "Origin": "https://login.inter-nation.uz",
        "Connection": "keep-alive",
        "Referer": "https://login.inter-nation.uz/?role=student",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    return header
