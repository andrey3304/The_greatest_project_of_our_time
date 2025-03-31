import re
import unicodedata
from data.classes import User
from database.db_session import create_session


def slugify(text):
    """
        Преобразует заданную строку в URL-пригодный слаг.

        Параметры:
        text (str): Входная строка для создания слага.

        Возвращает:
        str: Слаговая версия входной строки.
    """
    text = str(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8'))
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text


def register_user(username, password):
    """
        Регистрирует нового пользователя в базе данных.

        Эта функция проверяет, существует ли пользователь с указанным именем пользователя в базе данных.
        Если пользователь не существует, создается новый объект User с указанным именем пользователя и паролем,
        а затем добавляется в сеанс базы данных. Сеанс затем фиксируется для сохранения изменений.

        Параметры:
        username (str): Имя пользователя нового пользователя. Должно быть уникальным в базе данных.
        password (str): Пароль нового пользователя.

        Возвращает:
        None
    """
    session = create_session()
    existing_user = session.query(User).filter_by(username=username).first()
    if existing_user:
        pass
    else:
        new_user = User(username=username, password=password)
        session.add(new_user)
        session.commit()