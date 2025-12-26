from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from data import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def link_btn(chat_id):
    link_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Murphy-Homework Web-Site',
                    web_app=WebAppInfo(url=f'https://12b3492d0594.ngrok-free.app?chat_id={chat_id}')
                )
            ]
        ]
    )
    return link_button

@dp.message_handler(commands='start')
async def start_handler(message: types.Message):
    username = f"(@{message.from_user.username})" if message.from_user.username else ""
    text = f"""
👋 Hello, Dear: <b>{message.from_user.full_name}</b> {username}.
Welcome to our bot. Please click 'Murphy-Homework Web-Site' button, and start doing your Murphy-Homeworks.

✊ GOOD LUCK...!
"""
    await message.answer(text=text, reply_markup=await link_btn(message.chat.id), parse_mode='HTML')

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
