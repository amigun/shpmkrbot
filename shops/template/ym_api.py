# Импорт библиотек
from yoomoney import Client, Quickpay
from dotenv import load_dotenv
import os, random

# Подключаем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Создание основного класса "Счет"
class Bill():
    # Инициализируем переменные окружения
    token = os.environ.get('TOKEN_YOOMONEY')
    receiver = os.environ.get('RECEIVER_YOOMONEY')

    #token = '4100116970575627.D32E20F02D710CB8BF30E18F0A3366C606F52289447A49C02175B5259E5ADA41EAD220208C349CFF9465C7CF7CABD248D053B2C8C5A9A208D9B3081A4EA105C4BD6071689F6C0456CBB78CF17B3EA4B9A8B696080416694C74996ED049170B4FFDF4159F3E18ABE0430F28B159E38658BC3EA0E4BCF66E3BF76F5BAB5DADD03F'
    #receiver = '4100116970575627'

    client = Client(token)

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
    def to_invoice(self, item_title, item_price):
        quickpay = Quickpay(
                receiver=self.receiver,
                quickpay_form='shop',
                targets=item_title,
                paymentType='SB',
                sum=item_price,
                label=self.bill_id
                )

        return quickpay.redirected_url

    # Метод для просмотра статуса счета
    def status_invoice(self):
        history = self.client.operation_history(label=self.bill_id)

        return history.operations[0].status
