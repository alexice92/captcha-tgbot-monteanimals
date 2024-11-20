import random
import hashlib
from aiogram.types import InlineKeyboardButton

EMOJIS = ["🐶", "🐱", "🐵", "🦄", "🐔", "🦉", "🐢", "🦀", "🐟"]


def generate_hashed_emoji(emoji: str, salt: str) -> str:
    """Генерирует хэш для правильного ответа."""
    return hashlib.sha256(f"{emoji}{salt}".encode()).hexdigest()


def generate_emoji_options(salt: str):
    """Генерирует кнопки с эмодзи, включая правильный вариант."""
    correct_emoji = "🦎"  # Ящерица
    options = random.sample(EMOJIS, 4)
    options.insert(random.randint(0, len(options)), correct_emoji)  # Рандомная вставка ящерицы

    buttons = []
    for emoji in options:
        hashed_value = generate_hashed_emoji(emoji, salt)  # Хэшируем каждый вариант
        buttons.append(InlineKeyboardButton(text=emoji, callback_data=f"captcha_{hashed_value}"))

    return buttons, correct_emoji
