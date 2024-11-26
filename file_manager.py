import os

STOPLIST_FILE = "ModeratedUsers.txt"


def load_stoplist():
    """Загружает стоп-лист из файла"""
    if not os.path.exists(STOPLIST_FILE):
        return {}
    with open(STOPLIST_FILE, "r", encoding="utf-8") as file:
        stoplist = {}
        for line in file:
            parts = line.strip().split(" | ")
            if len(parts) == 3:
                user_id, username, full_name = parts
                stoplist[int(user_id)] = (username, full_name)
        return stoplist


def save_stoplist(stoplist):
    """Сохраняет стоп-лист в файл"""
    with open(STOPLIST_FILE, "w", encoding="utf-8") as file:
        for user_id, (username, full_name) in stoplist.items():
            file.write(f"{user_id} | {username} | {full_name}\n")


def add_to_stoplist(user_id, username, full_name):
    """Добавляет пользователя в стоп-лист"""
    stoplist = load_stoplist()
    stoplist[user_id] = (username, full_name)
    save_stoplist(stoplist)


def remove_from_stoplist(user_id):
    """Удаляет пользователя из стоп-листа"""
    stoplist = load_stoplist()
    if user_id in stoplist:
        del stoplist[user_id]
    save_stoplist(stoplist)


def is_in_stoplist(user_id):
    """Проверяет, находится ли пользователь в стоп-листе"""
    stoplist = load_stoplist()
    return user_id in stoplist
