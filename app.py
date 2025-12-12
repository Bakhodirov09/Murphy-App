from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from data import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def link_btn(chat_id):
    link_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Murphy-Homework Web-Site', web_app=WebAppInfo(url=f'https://uzb.uz?chat_id={chat_id}'))
            ]
        ]
    )
    return link_button

@dp.message_handler(commands='start')
async def start_handler(message: types.Message):
    text = "We are sorry, but we are adding questions to the Murphy-App for students, and working on its security. 🛡\nMurphy-App for students is ready: 87.5%."
#     text = f"""
# 👋 Hello, Dear: <b>{message.from_user.full_name}</b> {f'({message.from_user.username})' if message.from_user.username.startswith('@') else f'(@{message.from_user.username})' if message.from_user.username else ''}.
# Welcome to our bot. Please click 'Murphy-Homework Web-Site' button, and start doing your Murphy-Homeworks.
#
# ✊ GOOD LUCK...!
# """
    await message.answer(text=text)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)