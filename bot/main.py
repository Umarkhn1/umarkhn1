import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Хранилище данных пользователей (логины и пароли)
user_data = {}

# Класс состояний для FSM
class UserState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

# Главная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙ Управление данными")],
        [KeyboardButton(text="🌐 Открыть LMS", web_app=types.WebAppInfo(url="https://lms.tuit.uz/auth/login"))]
    ],
    resize_keyboard=True
)

# Клавиатура управления данными
data_management_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Мои данные")],
        [KeyboardButton(text="🗑 Удалить данные")],
        [KeyboardButton(text="➕ Добавить данные")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))  # Обработчик команды /start
async def start_command(message: Message):
    await message.answer("Привет! Я бот LMS. Выберите действие ниже.", reply_markup=main_keyboard)

@dp.message(lambda message: message.text == "⚙ Управление данными")
async def manage_data(message: Message):
    await message.answer("Выберите действие:", reply_markup=data_management_keyboard)

@dp.message(lambda message: message.text == "📋 Мои данные")
async def show_data(message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]:
        data_text = "\n".join([f"👤 {i+1}. Логин: {d['login']}, Пароль: {d['password']}" for i, d in enumerate(user_data[user_id])])
        await message.answer(f"📋 Ваши сохранённые данные:\n{data_text}")
    else:
        await message.answer("❌ У вас нет сохранённых данных.")

@dp.message(lambda message: message.text == "🗑 Удалить данные")
async def delete_data_menu(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or not user_data[user_id]:
        await message.answer("❌ У вас нет сохранённых данных для удаления.")
        return

    # Клавиатура с выбором логина для удаления
    buttons = [KeyboardButton(text=d['login']) for d in user_data[user_id]]
    buttons.append(KeyboardButton(text="🔙 Назад"))
    delete_keyboard = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)

    await message.answer("Выберите логин для удаления:", reply_markup=delete_keyboard)

@dp.message(lambda message: message.text in [d['login'] for d in user_data.get(message.from_user.id, [])])
async def delete_selected_data(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = [d for d in user_data[user_id] if d['login'] != message.text]

    await message.answer(f"✅ Данные для логина {message.text} удалены!", reply_markup=data_management_keyboard)

@dp.message(lambda message: message.text == "➕ Добавить данные")
async def add_data(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in user_data and len(user_data[user_id]) >= 3:
        await message.answer("❌ Вы можете сохранить только 3 логина!")
        return

    await message.answer("✍ Введите логин:")
    await state.set_state(UserState.waiting_for_login)  # Переключаемся в состояние ожидания логина

@dp.message(UserState.waiting_for_login)
async def get_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("🔒 Теперь введите пароль:")
    await state.set_state(UserState.waiting_for_password)  # Переход к следующему состоянию

@dp.message(UserState.waiting_for_password)
async def get_password(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    login = data['login']
    password = message.text

    if user_id not in user_data:
        user_data[user_id] = []
    user_data[user_id].append({"login": login, "password": password})

    await message.answer(f"✅ Данные сохранены!\n👤 Логин: {login}\n🔑 Пароль: {password}", reply_markup=data_management_keyboard)
    await state.clear()  # Очистка состояний

@dp.message(lambda message: message.text == "🔙 Назад")
async def go_back(message: Message):
    await message.answer("🔙 Возвращаемся в главное меню.", reply_markup=main_keyboard)

# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
