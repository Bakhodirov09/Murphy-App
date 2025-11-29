from environs import Env
from pytz import timezone

env = Env()
env.read_env()

# JWT (Json Web Tokens) Settings

SECRET_KEY = env.str('SECRET_KEY')
ALGORITHM = env.str('ALGORITHM')

# DB (DataBase) Settings
DB_USER = env.str('DB_USER')
DB_NAME = env.str('DB_NAME')
DB_PORT = env.int('DB_PORT')
DB_PASS = env.str('DB_PASS')
DB_HOST = env.str('DB_HOST')

# Get Student's data API url
LOGIN_INTER_URL = env.str('LOGIN_INTER_URL')
LOGIN_REQUEST_HEX_KEY = env.str('LOGIN_REQUEST_HEX_KEY')
LOGIN_RESPONSE_HEX_KEY = env.str('LOGIN_RESPONSE_HEX_KEY')
LOGIN_HEADER_HEX_KEY = env.str('LOGIN_HEADER_HEX_KEY')
LOGIN_SECRET_KEY = env.str('LOGIN_SECRET_KEY')
LOGIN_STATIC_STR = env.str('LOGIN_STATIC_STR')

# Timezone
tashkent = timezone("Asia/Tashkent")