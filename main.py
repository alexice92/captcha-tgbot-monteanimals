import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from datetime import datetime, timedelta

from captchaDB import generate_emoji_options, generate_hashed_emoji
from configs import API_TOKEN, CAPTCHA_TIMEOUT

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Словарь для хранения состояния новых пользователей
pending_users = {}


@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def on_new_member(message: types.Message):
    """Обрабатывает добавление нового участника"""
    try:
        new_member = message.new_chat_members[0]
        chat_id = message.chat.id
        user_id = new_member.id
        salt = str(random.randint(1000, 9999))  # Генерация случайной "соли"

        logging.info(f"Новый участник {new_member.full_name} добавлен в чат {chat_id}")

        # Ограничить нового участника
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )

        # Генерация кнопок с эмодзи
        buttons, correct_emoji = generate_emoji_options(salt)
        hashed_answer = generate_hashed_emoji(correct_emoji, salt)

        keyboard = InlineKeyboardMarkup(row_width=5)
        keyboard.add(*buttons)

        # Отправка сообщения с капчей
        msg = await message.reply(
            f"Привет, {new_member.first_name}! Выбери среди предложенных эмодзи 🦎 (ящерицу), чтобы подтвердить, что ты не спамер.",
            reply_markup=keyboard
        )

        # Сохранение данных о пользователе
        pending_users[user_id] = {
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "correct_hash": hashed_answer,
            "salt": salt,
            "expire_time": datetime.utcnow() + timedelta(seconds=CAPTCHA_TIMEOUT),
        }

        # Установить тайм-аут на ответ
        await asyncio.sleep(CAPTCHA_TIMEOUT)
        if user_id in pending_users and datetime.utcnow() > pending_users[user_id]["expire_time"]:
            logging.warning(f"Пользователь {new_member.full_name} не прошел проверку в течение времени.")
            await bot.send_message(
                chat_id,
                f"{new_member.first_name} не прошел проверку и остается с ограничениями."
            )
            del pending_users[user_id]

    except Exception as e:
        logging.error(f"Ошибка при обработке нового участника: {e}")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("captcha_"))
async def handle_captcha(callback_query: types.CallbackQuery):
    """Обрабатывает ответы на капчу"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data.split("_")
        hashed_value = data[1]
        target_user_id = int(data[2])

        # Проверка, что ответил именно новый участник
        if user_id != target_user_id:
            await callback_query.answer("Вы не можете отвечать на эту капчу.")
            logging.info(f"Пользователь {callback_query.from_user.full_name} пытался ответить за другого участника.")
            return

        # Проверка наличия участника в ожидании
        if user_id not in pending_users:
            await callback_query.answer("Капча уже завершена или не активна.")
            return

        user_data = pending_users[user_id]

        # Проверка времени истечения
        if datetime.utcnow() > user_data["expire_time"]:
            await callback_query.message.edit_text("Время на прохождение капчи истекло. Ты остаешься с ограничениями.")
            del pending_users[user_id]
            logging.warning(f"Пользователь {callback_query.from_user.full_name} не успел ответить.")
            return

        # Проверка правильного ответа
        if hashed_value == user_data["correct_hash"]:
            # Снять ограничения
            await bot.restrict_chat_member(
                user_data["chat_id"],
                user_id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await callback_query.message.edit_text("Капча пройдена! Добро пожаловать!")
            logging.info(f"Пользователь {callback_query.from_user.full_name} успешно прошел капчу.")
        else:
            await callback_query.message.edit_text("Неправильный ответ. Ты остаешься с ограничениями.")
            logging.warning(f"Пользователь {callback_query.from_user.full_name} дал неправильный ответ.")

        # Удалить пользователя из списка ожидания
        del pending_users[user_id]

    except Exception as e:
        logging.error(f"Ошибка при обработке капчи: {e}")


if __name__ == "__main__":
    from aiogram import asyncio  # Используем asyncio для таймеров
    executor.start_polling(dp, skip_updates=True)
