import random
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions, InlineKeyboardMarkup
from aiogram.utils import executor
from captcha_questions import generate_emoji_options, generate_hashed_emoji, CAPTCHA_QUESTION
from configs import API_TOKEN, CAPTCHA_TIMEOUT, MESSAGE_LIFETIME
from bot_responses import RESPONSES
from stoplist_manager import add_to_stoplist, remove_from_stoplist, is_in_stoplist

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Состояния участников
pending_users = {}
deleted_messages = set()


async def send_and_schedule_deletion(chat_id: int, text: str, delay: int = MESSAGE_LIFETIME):
    """Отправляет сообщение и планирует его удаление через заданное время."""
    try:
        msg = await bot.send_message(chat_id, text)
        logging.debug(f"Отправлено сообщение (ID: {msg.message_id}) с текстом: {text}")
        if delay > 0:
            asyncio.create_task(delete_message_with_delay(chat_id, msg.message_id, delay))
        return msg
    except Exception as e:
        logging.warning(f"Не удалось отправить сообщение: {e}")


async def delete_message_with_delay(chat_id: int, message_id: int, delay: int):
    """Удаляет сообщение через заданную задержку."""
    await asyncio.sleep(delay)
    if message_id in deleted_messages:
        logging.debug(f"Сообщение {message_id} уже было удалено ранее.")
        return
    try:
        await bot.delete_message(chat_id, message_id)
        deleted_messages.add(message_id)
        logging.debug(f"Сообщение {message_id} удалено через {delay} секунд.")
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение {message_id}: {e}", exc_info=True)


def remove_pending_user(user_id: int):
    """Удаляет пользователя из ожидающих капчу."""
    if user_id in pending_users:
        del pending_users[user_id]
        logging.debug(f"Пользователь {user_id} удалён из pending_users.")


async def delete_user_messages(chat_id: int, user_id: int):
    """Удаляет все связанные с пользователем сообщения."""
    if user_id not in pending_users:
        return
    user_data = pending_users[user_id]
    for message_id in user_data.get("messages", []):
        if message_id in deleted_messages:
            continue
        try:
            await bot.delete_message(chat_id, message_id)
            deleted_messages.add(message_id)
        except Exception:
            pass
    remove_pending_user(user_id)


# --- Обработка нового участника ---
async def is_user_in_stoplist(chat_id: int, user_id: int, username: str, full_name: str):
    """Проверяет участника на наличие в файле стоп-листа."""
    if is_in_stoplist(chat_id, user_id):
        logging.info(f"Пользователь {user_id} уже в стоп-листе.")
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await send_and_schedule_deletion(
            chat_id,
            RESPONSES["captcha_unavailable"].format(name=full_name)
        )
        return True
    return False


async def send_captcha(chat_id: int, new_member: types.User):
    """Отправляет капчу новому участнику."""
    user_id = new_member.id
    salt = str(random.randint(1000, 9999))
    buttons, correct_emoji = generate_emoji_options(salt)
    hashed_answer = generate_hashed_emoji(correct_emoji, salt)[:32]

    keyboard = InlineKeyboardMarkup(row_width=len(buttons))
    keyboard.row(*buttons)

    msg = await bot.send_message(
        chat_id,
        CAPTCHA_QUESTION.format(name=new_member.first_name),
        reply_markup=keyboard
    )

    pending_users[user_id] = {
        "chat_id": chat_id,
        "message_id": msg.message_id,
        "messages": [msg.message_id],
        "correct_hash": hashed_answer,
        "expire_time": datetime.utcnow() + timedelta(seconds=CAPTCHA_TIMEOUT),
        "first_name": new_member.first_name,
        "full_name": new_member.full_name,
        "username": f"@{new_member.username}" if new_member.username else "нет_ника",
        "interacted": False,  # Пользователь еще не взаимодействовал
    }
    logging.info(f"Капча для пользователя {new_member.full_name} отправлена (ID сообщения: {msg.message_id}).")
    add_to_stoplist(chat_id, user_id, username=new_member.username, full_name=new_member.full_name)
    asyncio.create_task(delete_user_messages_after_timeout(chat_id, user_id))


async def delete_user_messages_after_timeout(chat_id: int, user_id: int, delay: int = 0):
    """Удаляет капчу и связанные с ней сообщения после таймаута."""
    await asyncio.sleep(CAPTCHA_TIMEOUT)
    if user_id in pending_users:
        user_data = pending_users[user_id]

        # Проверяем, взаимодействовал ли пользователь с капчей
        if not user_data.get("interacted", False):
            # Удаляем сообщения капчи
            await delete_user_messages(chat_id, user_id)

            # Отправляем сообщение о таймауте
            timeout_message = await send_and_schedule_deletion(chat_id, RESPONSES["captcha_timeout_message"].format(name=user_data["first_name"]))
            logging.info(f"Сообщение о таймауте (ID: {timeout_message.message_id}) отправлено для пользователя {user_id}.")
        else:
            logging.info(f"Пользователь {user_id} взаимодействовал с капчей, сообщение о таймауте не отправлено.")

        # Удаляем пользователя из pending_users
        remove_pending_user(user_id)


# --- Обработка капчи ---
@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def on_new_member(message: types.Message):
    """Обрабатывает событие добавления нового участника."""
    chat_id = message.chat.id

    for new_member in message.new_chat_members:
        user_id = new_member.id
        username = f"@{new_member.username}" if new_member.username else "нет_ника"
        full_name = new_member.full_name or "нет_имени"

        if await is_user_in_stoplist(chat_id, user_id, username, full_name):
            continue

        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await send_captcha(chat_id, new_member)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("captcha_"))
async def on_captcha_response(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Проверка: принадлежит ли капча текущему пользователю
    if user_id not in pending_users:
        await callback_query.answer(RESPONSES["captcha_inactive"], show_alert=True)
        logging.warning(f"Пользователь {user_id} попытался пройти чужую капчу.")
        return

    user_data = pending_users[user_id]

    # Логирование после определения user_id
    logging.debug(f"Проверка пользователя {user_id} ({user_data.get('username')}, {user_data.get('full_name')}) на соответствие.")


    # Проверка, что это именно сообщение пользователя
    if callback_query.message.message_id != user_data["message_id"]:
        await callback_query.answer(RESPONSES["captcha_inactive"], show_alert=True)
        logging.warning(f"Пользователь {user_id} попытался взаимодействовать с чужой капчей.")
        return

    # Проверка правильного хэша
    hashed_value = callback_query.data.split("_")[1]
    if hashed_value != user_data["correct_hash"]:
        # Неверный ответ
        failed_message = await bot.edit_message_text(
            RESPONSES["captcha_failed"].format(name=user_data["first_name"]),
            chat_id,
            user_data["message_id"]
        )
        logging.warning(f"Пользователь {user_id} ({user_data['first_name']}) провалил капчу.")
        asyncio.create_task(delete_message_with_delay(chat_id, failed_message.message_id, MESSAGE_LIFETIME))
    else:
        # Успешный ответ
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_other_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_voice_notes=True,
                can_send_video_notes=True,
                can_add_link_previews=True,
                can_send_polls=True,
                can_invite_users=True
            )
        )

        # Удаление из стоп-листа
        if remove_from_stoplist(chat_id, user_id):  # Перемещено сюда
            logging.info(f"Пользователь {user_id} удален из стоп-листа после успешного прохождения капчи.")
        else:
            logging.warning(f"Не удалось удалить пользователя {user_id} из стоп-листа.")

        welcome_message = await bot.edit_message_text(
            RESPONSES["captcha_passed"].format(name=user_data["first_name"]),
            chat_id,
            user_data["message_id"]
        )
        logging.info(f"Пользователь {user_id} ({user_data['first_name']}) успешно прошел капчу.")
        asyncio.create_task(delete_message_with_delay(chat_id, welcome_message.message_id, MESSAGE_LIFETIME))

    # Удаляем данные о пользователе
    del pending_users[user_id]

    # Удаление связанных сообщений после задержки
    asyncio.create_task(delete_user_messages_after_timeout(chat_id, user_id, MESSAGE_LIFETIME))


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
