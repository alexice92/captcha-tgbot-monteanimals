import random
import hashlib
from aiogram.types import InlineKeyboardButton

# Список эмодзи для капчи
EMOJIS = ["🐶", "🐱", "🐵", "🦄", "🐔", "🦉", "🐢", "🦀", "🐟"]

# Вопрос для прохождения капчи
CAPTCHA_QUESTION = (
    "Привет, {name}! Выбери среди предложенных эмодзи зеленую ящерицу 🦎 , чтобы подтвердить, что ты не спамер."
)


def generate_hashed_emoji(emoji: str, salt: str) -> str:
    """Генерирует компактный хэш для правильного ответа."""
    return hashlib.md5(f"{emoji}{salt}".encode()).hexdigest()


def generate_emoji_options(salt: str):
    """Генерирует кнопки с эмодзи, включая правильный вариант."""
    correct_emoji = "🦎"  # Ящерица
    options = random.sample(EMOJIS, 4)  # Выбираем 4 случайных эмодзи из списка
    random_position = random.randint(0, len(options))  # Генерируем случайную позицию для ящерицы
    options.insert(random_position, correct_emoji)  # Вставляем ящерицу в случайную позицию

    buttons = []  # Список кнопок
    for emoji in options:
        hashed_value = generate_hashed_emoji(emoji, salt)  # Хэшируем каждый вариант
        buttons.append(InlineKeyboardButton(text=emoji, callback_data=f"captcha_{hashed_value}"))

    return buttons, correct_emoji
