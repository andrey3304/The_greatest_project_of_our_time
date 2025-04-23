import random
import re, datetime
import unicodedata
'''from data.classes import User
from database.db_session import create_session'''
from slugify import slugify


def make_slug(text):
    """
    Создает слаг из текста, транслитерируя кириллицу в латиницу и удаляя недопустимые символы.
    """
    text = str(text).lower()  # Преобразуем в строку, если это необходимо

    # Транслитерация кириллицы в латиницу с помощью python-slugify
    slug = slugify(text) # to_lower=True преобразует все в нижний регистр

    # Удаляем повторяющиеся дефисы (если они остались после slugify)
    slug = re.sub(r"-+", "-", slug)

    # Удаляем дефисы в начале и конце строки
    slug = slug.strip("-")

    return slug



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


def generate_equation_for_captcha():
    """
    Генерирует простое математическое уравнение для использования в CAPTCHA.
    
    Создает уравнение с двумя случайными числами и случайным оператором (+, -, *).
    Числа выбираются в диапазоне от 1 до 18 для первого числа и от 1 до 10 для второго.
    
    Возвращает:
        tuple: Кортеж содержащий строку с уравнением и правильный ответ на него.
               Пример: ("5 + 3", 8)
    """
    a = random.randint(10, 18)
    b = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])

    if operation == '+':
        answer = a + b
        equation = f"{a} + {b}"
    elif operation == '-':
        answer = a - b
        equation = f"{a} - {b}"
    else:
        answer = a * b
        equation = f"{a} × {b}"

    return equation, answer


def generate_name_for_avatar_photo(user_id, filename):
    """
    Генерирует уникальное имя файла для аватарки пользователя.
    
    Имя формируется из:
    - ID пользователя
    - Текущей даты и времени в формате YYYYMMDDHHMMSS
    - Случайного числа от 0 до 9
    - Расширения исходного файла
    
    Параметры:
        user_id (int): ID пользователя
        filename (str): Исходное имя файла для извлечения расширения
        
    Возвращает:
        str: Уникальное имя файла в формате {user_id}{timestamp}{random}.{ext}
    """
    name_for_fut_file = (str(user_id) + str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")) +
                         str(random.randint(0, 9)))
    ext = filename.rsplit('.', 1)[1].lower()
    return f'{name_for_fut_file}.{ext}'


def allowed_file(filename):
    """
    Проверяет, является ли расширение файла разрешенным для загрузки.
    
    Разрешенные расширения: png, jpg, jpeg, webp
    
    Параметры:
        filename (str): Имя файла для проверки
        
    Возвращает:
        bool: True если расширение разрешено, False в противном случае
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'webp'}


print(make_slug('It'))