# Импорт библиотек
from datetime import datetime
from dotenv import load_dotenv
import requests, random, json, os

# Подключаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Создание основного класса "Счет"
class Bill():
    # Инициализируем переменные окружения
    public = os.environ.get('TOKEN_QIWI_PUBLIC')
    private = os.environ.get('TOKEN_QIWI_PRIVATE')

    # Генерация уникального bill_id
    bill_id = ''
    for rand in range(10):
        list_symbols = ['0', '1', '2', '3', '4', '5', '6', '7',
                        '8', '9', 'a', 'b', 'c', 'd', 'e', 'f',
                        'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                        'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                        'w', 'x', 'y', 'z']
        bill_id += random.choice(list_symbols) + random.choice(list_symbols) + '-'
    bill_id = bill_id[:-1]

    # Метод выставления счета
    def to_invoice(self, private, bill_id, value):
        # Генерация expirationDateTime
        current_datetime = datetime.now()
        year = current_datetime.year
        month = current_datetime.month + 1
        day = current_datetime.day
        hour = current_datetime.hour
        minute = current_datetime.minute
        second = current_datetime.second

        expirationDateTime = f'{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}+03:00'

        # Заголовки запроса
        headers = {'Accept': 'application/json',
                    'Authorization': 'Bearer ' + private,
                    'Content-type': 'application/json'}

        # Параметры запросы
        params = {'amount': {'value': value, 'currency': 'RUB'},
                'expirationDateTime': expirationDateTime}

        # Перевод из str в json (dict)
        params = json.loads(json.dumps(params))

        # Выполнение запроса
        r = requests.put(f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}', json=params, headers=headers)

        return r.json()['payUrl']

    # Метод для просмотра статуса счета
    def status_invoice(self, private, bill_id):
        # Заголовки запроса
        headers = {'Authorization': 'Bearer ' + private,
                    'Accept': 'application/json'}

        # Выполнение запроса
        r = requests.get(f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}', headers=headers)

        return r.json()['status']['value']
