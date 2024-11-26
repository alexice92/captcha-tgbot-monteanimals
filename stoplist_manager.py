import os
import csv
import logging

STOPLIST_FILE = "stoplist.csv"

def load_stoplist():
    """Загружает стоп-лист из файла."""
    stoplist = {}
    if not os.path.exists(STOPLIST_FILE):
        return stoplist
    try:
        with open(STOPLIST_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 4:
                    continue
                chat_id, user_id, username, first_name = row
                if chat_id not in stoplist:
                    stoplist[chat_id] = {}
                stoplist[chat_id][user_id] = {
                    "username": username,
                    "first_name": first_name,
                }
    except Exception as e:
        logging.error(f"Ошибка загрузки стоп-листа: {e}")
    return stoplist

def save_stoplist(stoplist):
    """Сохраняет стоп-лист в файл."""
    try:
        with open(STOPLIST_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for chat_id, users in stoplist.items():
                for user_id, data in users.items():
                    writer.writerow([chat_id, user_id, data.get("username", ""), data.get("first_name", "")])
    except Exception as e:
        logging.error(f"Ошибка сохранения стоп-листа: {e}")

def add_to_stoplist(chat_id: int, user_id: int, username: str = None, full_name: str = None):
    """Добавляет пользователя в стоп-лист чата."""
    username = username or "нет_ника"
    full_name = full_name or "нет_имени"

    try:
        with open(STOPLIST_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([chat_id, user_id, username, full_name])
            logging.info(f"Пользователь {user_id} добавлен в стоп-лист чата {chat_id}.")
    except Exception as e:
        logging.error(f"Ошибка добавления пользователя {user_id} в стоп-лист: {e}")

def remove_from_stoplist(chat_id: int, user_id: int):
    """Удаляет пользователя из стоп-листа чата."""
    temp_file = STOPLIST_FILE + ".tmp"
    removed = False

    try:
        with open(STOPLIST_FILE, mode="r", newline="", encoding="utf-8") as file, \
             open(temp_file, mode="w", newline="", encoding="utf-8") as temp:
            reader = csv.reader(file)
            writer = csv.writer(temp)

            for row in reader:
                if len(row) < 4:
                    logging.warning(f"Пропуск некорректной строки: {row}")
                    continue
                if int(row[0]) == chat_id and int(row[1]) == user_id:
                    removed = True
                    logging.info(f"Удалена строка: {row}")
                else:
                    writer.writerow(row)

        os.replace(temp_file, STOPLIST_FILE)
    except Exception as e:
        logging.error(f"Ошибка удаления пользователя {user_id} из стоп-листа: {e}")

    return removed


def is_in_stoplist(chat_id: int, user_id: int) -> bool:
    """Проверяет, находится ли пользователь в стоп-листе."""
    try:
        with open(STOPLIST_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 4:
                    continue
                if int(row[0]) == chat_id and int(row[1]) == user_id:
                    return True
    except Exception as e:
        logging.error(f"Ошибка проверки стоп-листа: {e}")
    return False
