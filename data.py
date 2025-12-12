import datetime

from environs import Env
from pydantic.v1.datetime_parse import datetime_re

env = Env()
env.read_env()

BOT_TOKEN = env.str('BOT_TOKEN')

import calendar
from datetime import date

weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Misol uchun 49 hafta bor deb olayapmiz
current_index = 0           # Qaysi weekdan boshlashni ko'rsatadi

def get_weeks_for_month(year, month):
    global current_index

    # Oydagi nechta hafta borligini hisoblaymiz
    cal = calendar.monthcalendar(year, month)
    week_count = len(cal)   # shu oy nechta hafta bor

    # week slice
    start = current_index
    end = current_index + week_count
    current_index = end     # keyingi oy mana shu joydan davom etadi

    return weeks[start:end]