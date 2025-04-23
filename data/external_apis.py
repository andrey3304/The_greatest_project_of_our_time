import requests
from data.config import WEATHER_API_KEY


class WeatherApiClient:
    """Клиент для работы с API сервиса погоды WeatherAPI.com."""
    def __init__(self):
        self.api_key = WEATHER_API_KEY
        self.base_url = 'http://api.weatherapi.com/v1/current.json'

    def get_city_weather_info(self, city):
        """Получает текущую погодную информацию для указанного города.

        Args:
            city (str): Название города для запроса погоды.

        Returns:
            dict: Словарь с погодными данными, содержащий:
                - city (str): Название города
                - country (str): Страна
                - localtime (str): Локальное время
                - temp (float): Температура в °C
                - text (str): Текстовое описание погоды
                - wind (float): Скорость ветра в mph
            str: Строка 'Error' в случае ошибки парсинга ответа
            str: Строка 'error' в случае HTTP ошибки

        Note:
            Язык ответа всегда русский ('lang': 'ru' в параметрах запроса)
        """
        params = {'key': self.api_key, 'q': city, 'lang': 'ru'}
        res = requests.get(self.base_url, params=params)
        if res.status_code == 200:
            answer = res.json()
            try:
                result = {
                    'city': answer['location']['name'],
                    'country': answer['location']['country'],
                    'localtime': answer['location']['localtime'],
                    'temp': answer['current']['temp_c'],
                    'text': answer['current']['condition']['text'],
                    'wind': answer['current']['wind_mph']
                }
            except:
                result = 'Error'
            return result
        else:
            return 'error'


