import re

import unicodedata


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