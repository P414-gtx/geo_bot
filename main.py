import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
import json
import os

BLOCKED_USERS_FILE = "blocked_users.json"
COORDINATES_FILE = "coordinates.json"
API_TOKEN = ''


EXPECTED_LATITUDE = 00.000000 
EXPECTED_LONGITUDE = 00.000000
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
    keyboard = get_welcome_keyboard()
    
    await message.reply("Мне нужна информация о местоположении одной из военных баз, но я не помню даже ее названия(\n"
                        "Хотя, есть некоторые факты, которые я все же запомнил (см. описание).\n", reply_markup=keyboard)

@dp.message(lambda message: message.text == "ОПИСАНИЕ")
async def send_description(message: types.Message):
    await bot.send_message(
        message.from_user.id,
        "Эта база имеет площадь почти 4 кв.км., является одной из крупнейших в Европе, а построили ее после каких-то известных трагических событий.... "
    )

    photo = FSInputFile("photo.jpg")
    await bot.send_photo(message.from_user.id, photo, disable_notification=True)


def load_blocked_users():
    if os.path.exists(BLOCKED_USERS_FILE):
        with open(BLOCKED_USERS_FILE, "r") as file:
            return set(json.load(file))
    return set()

def save_blocked_users():
    with open(BLOCKED_USERS_FILE, "w") as file:
        json.dump(list(blocked_users), file)

blocked_users = load_blocked_users()

def load_coordinates():
    if os.path.exists(COORDINATES_FILE):
        with open(COORDINATES_FILE, "r") as file:
            return json.load(file)
    return {}

coordinates_data = load_coordinates()

@dp.message(lambda message: message.text == "ПРОВЕРКА")
async def start_checking(message: types.Message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        await message.reply("Вы заблокированы и не можете отправлять координаты.")
        return

    if user_id not in attempt_counts:
        attempt_counts[user_id] = 0
    
    if attempt_counts[user_id] < 5:
        await message.reply("Пожалуйста, отправьте свои координаты и страну в формате: широта, долгота, страна. Например: 40.7128,-74.0060, США")
    else:
        blocked_users.add(user_id)
        save_blocked_users()
        await message.reply("Вы исчерпали все попытки. Вы заблокированы.")

@dp.message()
async def check_coordinates(message: types.Message):
    user_id = message.from_user.id

    if user_id in blocked_users:
        await message.reply("Вы заблокированы и не можете отправлять координаты.")
        return

    if user_id not in attempt_counts:
        attempt_counts[user_id] = 0

    try:
        lat, lon, country = message.text.split(',')
        lat = float(lat)
        lon = float(lon)
        country = country.strip()

        if country in coordinates_data:
            expected_lat, expected_lon = coordinates_data[country]
            if lat == expected_lat and lon == expected_lon:
                await message.reply(f"Координаты успешно получены! Флаг: {FLAG}")
                return
        await message.reply(f"Неверные координаты или страна. Попробуйте еще раз.")
        
    except ValueError:
        pass

    attempt_counts[user_id] += 1
    if attempt_counts[user_id] >= 5:
        blocked_users.add(user_id)
        save_blocked_users()
        await message.reply("Вы исчерпали все попытки. Вы заблокированы.")
    else:
        attempts_left = 5 - attempt_counts[user_id]
        await message.reply(f"Неверные координаты. Попробуйте еще раз. Осталось попыток: {attempts_left}")

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
