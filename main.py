
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = ''

EXPECTED_LATITUDE = 40.7128  
EXPECTED_LONGITUDE = -74.0060  
FLAG = "vka{xxxxxxxxxxxxxxxxxxxxxxx}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

attempt_counts = {}
blocked_users = set() 

def get_welcome_keyboard():

    button_description = KeyboardButton(text="ОПИСАНИЕ")
    button_check = KeyboardButton(text="ПРОВЕРКА")
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_description, button_check]], 
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Приветственное сообщение с кнопками"""
    keyboard = get_welcome_keyboard()
    
    await message.reply("Здравствуйте! Это тестовый бот.\n"
                        "Выберите одну из опций ниже:", reply_markup=keyboard)

@dp.message(lambda message: message.text == "ОПИСАНИЕ")
async def send_description(message: types.Message):
    """Отправка описания и изображения"""
    await message.answer("Это пример описания.")
    await message.answer_photo('map.jpg')  

@dp.message(lambda message: message.text == "ПРОВЕРКА")
async def start_checking(message: types.Message):
    """Запуск проверки координат"""
    user_id = message.from_user.id
    if user_id in blocked_users:
        await message.reply("Вы заблокированы и не можете отправлять координаты.")
        return

    if user_id not in attempt_counts:
        attempt_counts[user_id] = 0
    
    if attempt_counts[user_id] < 3:
        await message.reply("Пожалуйста, отправьте свои координаты (широта и долгота). Например: 40.7128,-74.0060")
    else:
        await message.reply("Вы исчерпали все попытки. Вы заблокированы.")
        blocked_users.add(user_id)  

@dp.message()
async def check_coordinates(message: types.Message):
    """Проверка координат пользователя"""
    user_id = message.from_user.id

    if user_id in blocked_users:
        await message.reply("Вы заблокированы и не можете отправлять координаты.")
        return

    if user_id not in attempt_counts:
        attempt_counts[user_id] = 0

    try:
        lat, lon = map(float, message.text.split(','))
        
        if lat == EXPECTED_LATITUDE and lon == EXPECTED_LONGITUDE:
            await message.reply(f"Координаты успешно получены! Флаг: {FLAG}")
            return
    except ValueError:
        pass

    attempt_counts[user_id] += 1
    if attempt_counts[user_id] >= 3:
        await message.reply("Вы исчерпали все попытки. Вы заблокированы.")
        blocked_users.add(user_id)
    else:
        attempts_left = 3 - attempt_counts[user_id]
        await message.reply(f"Неверные координаты. Попробуйте еще раз. Осталось попыток: {attempts_left}")

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
