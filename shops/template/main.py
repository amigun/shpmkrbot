# Импортируем нужные библиотеки
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from datetime import datetime
from threading import Thread
from qiwi_api import Bill
import sqlite3, os, sys, time, re, random, asyncio, ym_api

# Получаем id создателя магазина и id самого магазина из аргументов командной строки
id_owner = sys.argv[1]
id_shop = sys.argv[2]

# Создаем базу данных
db = sqlite3.connect('database.db', check_same_thread = False)
sql = db.cursor()

# Создаем локальную базу данных
db_l = sqlite3.connect(f'shops/{id_owner}_{id_shop}/database.db', check_same_thread = False)
sql_l = db_l.cursor()

sql.execute(f"SELECT name_shop FROM shops WHERE id_shop = {id_shop}")
name_shop = sql.fetchone()[0]

sql.execute(f"SELECT token_bot FROM shops WHERE id_shop = {id_shop}")
TOKEN = sql.fetchone()[0]

# Инициализируем бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Создаем глобальные переменные
ref_system = 0
support = '-'
coupon = '-'
last_message = datetime.now()

# Функция ожидания остановки
async def listening():
    is_quit = 0 # По умолчанию, выходить не надо

    while is_quit != 1: # Пока is_quit не станет 1 (пока не надо будет выйти)
        sql.execute(f"SELECT is_del FROM is_dp WHERE id_shop = {id_shop}")
        is_del = sql.fetchone()[0]

        sql.execute(f"SELECT is_pause FROM is_dp WHERE id_shop = {id_shop}")
        is_pause = sql.fetchone()[0]

        if is_del == 1 or is_pause == 1:
            is_quit = 1

        await asyncio.sleep(10)

    os._exit(0) # Завершить работу магазина

# Функция для рассылки
async def newsletter():
    global id_shop
    while True:
        text = ''

        with open(f'newsletter/newsletter{id_shop}.txt', 'r') as f:
            text = f.read()

        if text == '' or text == '\n' or text == '\n\n':
            await asyncio.sleep(5)
        else:
            sql_l.execute(f"SELECT id_user FROM users")
            all_users = sql_l.fetchall()

            for user in all_users:
                await bot.send_message(user[0], text)
                await asyncio.sleep(1)

            with open(f'newsletter/newsletter{id_shop}.txt', 'w') as f:
                f.write('')

# Функция для глобальной рассылки
async def global_newsletter():
    global id_shop

    while True:
        text = ''

        with open(f'newsletter/newsletter.txt', 'r') as f:
            text = f.read()

        if text == '' or text == '\n' or text == '\n\n':
            await asyncio.sleep(5)
        else:
            sql.execute(f"SELECT newsletter FROM shops WHERE id_shop = {id_shop}")
            newsletter = sql.fetchone()[0]

            if newsletter == 0:
                sql_l.execute(f"SELECT id_user FROM users")
                all_users = sql_l.fetchall()

                sql.execute(f"UPDATE shops SET newsletter = 1 WHERE id_shop = {id_shop}")
                db.commit()

                for user in all_users:
                    await bot.send_message(user[0], text)
                    await asyncio.sleep(0.2)

async def time_comparison():
    while True:
        global id_shop
        global id_owner
        global last_message
        now = datetime.now()

        diff = (now - last_message).seconds

        if diff >= 172800:
            await bot.send_message(id_owner, f'🤓 Ваш магазин был остановлен в связи с неактивностью. Вы можете заново включить бота в настройках')

            sql.execute(f"UPDATE is_dp SET is_pause = 1 WHERE id_shop = {id_shop}")
            db.commit()

        await asyncio.sleep(3600)

# Запускаю отдельный поток
#thread_listen = Thread(target=listening)
#thread_listen.start()

# Запускаю отдельный поток
loop = asyncio.get_event_loop()
loop.create_task(newsletter())
loop.create_task(global_newsletter())
loop.create_task(listening())
loop.create_task(time_comparison())

# Приветственное сообщение
@dp.message_handler(commands=['start'], state='*')
async def process_start_command(msg: types.Message):
    global last_message

    last_message = msg.date

    id_ref = 0 # По умолчанию - ref_id равен 0

    sql_l.execute(f"SELECT * FROM users WHERE id_user = {msg.from_user.id}")

    if sql_l.fetchone() is None: # Если пользователь запускает бота в первый раз
        try:
            id_ref = int((msg.text).split()[1]) # Если он запускает по реферальной ссылке
        except IndexError:
            pass

        if id_ref != 0:
            sql_l.execute(f"SELECT count_ref FROM users WHERE id_user = {id_ref}")
            count_ref = int(sql_l.fetchone()[0])
            count_ref += 1

            sql_l.execute(f"UPDATE users SET count_ref = {count_ref} WHERE id_user = {id_ref}")
            db_l.commit()

    main_menu__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    main_menu__button_1 = KeyboardButton('⭐️ Все товары')
    main_menu__button_2 = KeyboardButton('👦 Профиль')
    main_menu__button_3 = KeyboardButton('👥 Реферальная система')
    main_menu__button_4 = KeyboardButton('🔧 Тех. поддержка')
    main_menu__button_5 = KeyboardButton('🎟 Актуальный купон')

    main_menu__kb.add(main_menu__button_1, main_menu__button_2)

    global ref_system
    global support
    global coupon

    try:
        sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
        ref_system = sql.fetchone()[0]

        sql.execute(f"SELECT support FROM shops WHERE id_shop = {id_shop}")
        support = sql.fetchone()[0]

        sql.execute(f"SELECT actual_coupon FROM shops WHERE id_shop = {id_shop}")
        coupon = sql.fetchone()[0]
    except TypeError:
        pass

    if ref_system != 0:
        main_menu__kb.add(main_menu__button_3)

    if support != '-':
        main_menu__kb.add(main_menu__button_4)

    if coupon != '-':
        main_menu__kb.add(main_menu__button_5)

    await bot.send_message(msg.from_user.id, f'👋Добро пожаловать в <b>{name_shop}</b>, {msg.from_user.first_name}!', reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
    await bot.send_message(msg.from_user.id, f'Чтобы сделать заказ, выбери кнопку «⭐️ Все товары», затем выбери категорию и сам товар!', reply_markup=main_menu__kb)

    # Создаем строку в бд о пользователе
    sql_l.execute(f"SELECT id_user FROM users WHERE id_user = '{msg.from_user.id}'")
    if sql_l.fetchone() is None:
        sql_l.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (msg.from_user.id, 0, 0, 0, 0, int(id_ref)))
        db_l.commit()

@dp.message_handler()
async def all_items(msg: types.Message):
    global id_shop
    global ref_system
    global last_message

    last_message = msg.date

    if msg.text == '⭐️ Все товары':
        category_callback = CallbackData('category', 'id_c')

        sql.execute(f"SELECT * FROM categories WHERE id_shop = {id_shop}")
        list_category_from_db = sql.fetchall()

        pre_list_category = [[idc[1] for idc in list_category_from_db], [name[2] for name in list_category_from_db]]

        list_category = []

        for i in range(len(pre_list_category[0])):
            list_category.append([InlineKeyboardButton(text=pre_list_category[1][i], callback_data=category_callback.new(id_c=pre_list_category[0][i]))])

        choice_category = InlineKeyboardMarkup(inline_keyboard = [x for x in list_category])

        if list_category == []:
            await bot.send_message(msg.from_user.id, f'🥺 Категории и товары в этом магазине отсутствуют')
        else:
            await bot.send_message(msg.from_user.id, f'🔥 Ниже представлен список доступных категорий. Выбери любую, чтобы посмотреть находящиеся в ней товары!', reply_markup=choice_category)
    elif msg.text == '👦 Профиль':
        sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
        ref_system = sql.fetchone()[0]

        sql_l.execute(f"SELECT * FROM users WHERE id_user = {msg.from_user.id}")
        user_info = sql_l.fetchall()[0]

        if ref_system != 0:
            await bot.send_message(msg.from_user.id, f'👤 <b>Пользователь:</b> {msg.from_user.first_name}\n🐚 <b>Куплено товаров:</b> {user_info[1]}\n👫 <b>Количество рефералов:</b> {user_info[2]}\n💎 <b>Заработано на рефералах:</b> {user_info[3]} руб.\n💸 <b>Реферальный баланс:</b> {user_info[4]} руб.', parse_mode='HTML')
        else:
            await bot.send_message(msg.from_user.id, f'👤 <b>Пользователь:</b> {msg.from_user.first_name}\n🐚 <b>Куплено товаров:</b> {user_info[1]}', parse_mode='HTML')
    elif msg.text == '👥 Реферальная система':
        sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
        ref_percent = sql.fetchone()[0]

        ref_link = CallbackData('ref_link', 'id_s')

        get_ref_link = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='🔶 Получить реферальную ссылку', callback_data=ref_link.new(id_s=id_shop))]])

        await bot.send_message(msg.from_user.id, f'🔺 В нашем магазине существует реферальная система! Привлекай клиентов в наш магазин и получай <b>{ref_percent}%</b> с каждой их покупки на свой реферальный баланс, который можешь потратить на внутренние покупки', reply_markup=get_ref_link, parse_mode='HTML')
    elif msg.text == '🔧 Тех. поддержка':
        sql.execute(f"SELECT support FROM shops WHERE id_shop = {id_shop}")

        support = sql.fetchone()[0]

        await bot.send_message(msg.from_user.id, support)
    elif msg.text == '🎟 Актуальный купон':
        sql.execute(f"SELECT actual_coupon FROM shops WHERE id_shop = {id_shop}")

        actual_coupon = sql.fetchone()[0]

        await bot.send_message(msg.from_user.id, actual_coupon)

@dp.callback_query_handler(lambda callback_query: True)
async def inline_button(call: types.CallbackQuery):
    global id_shop
    await call.answer(cache_time=2)
    global last_message

    r = re.findall(r'([a-z_]*):([0-9]*)', call.data)

    last_message = call.message.date

    bot_name = await bot.get_me()

    if r[0][0] == 'category':
        id_category = int(r[0][1])

        item_callback = CallbackData('item', 'id_c', 'id_i')

        sql.execute(f"SELECT * FROM items WHERE id_category = {id_category}")
        list_items_from_db = sql.fetchall()

        pre_list_items = [[idi[1] for idi in list_items_from_db], [name[2] for name in list_items_from_db]]

        list_items = []

        for i in range(len(pre_list_items[0])):
            list_items.append([InlineKeyboardButton(text=pre_list_items[1][i], callback_data=item_callback.new(id_c=id_category, id_i=pre_list_items[0][i]))])

        cb_data = CallbackData('back_to_categories', 'id_s')

        list_items.append([InlineKeyboardButton(text='◀️ Назад', callback_data=cb_data.new(id_s=id_shop))])

        choice_item = InlineKeyboardMarkup(inline_keyboard = [x for x in list_items])

        if len(list_items) == 1: # Если в клавиатуре только одна кнопка - "Назад"
            await call.message.edit_text(f'🥺 Товары в этой категории отсутствуют', reply_markup=choice_item)
        else:
            await call.message.edit_text(f'💥 Ниже список товаров выбранной вами категории', reply_markup=choice_item)
    elif r[0][0] == 'back_to_categories':
        category_callback = CallbackData('category', 'id_c')

        sql.execute(f"SELECT * FROM categories WHERE id_shop = {id_shop}")
        list_category_from_db = sql.fetchall()

        pre_list_category = [[idc[1] for idc in list_category_from_db], [name[2] for name in list_category_from_db]]

        list_category = []

        for i in range(len(pre_list_category[0])):
            list_category.append([InlineKeyboardButton(text=pre_list_category[1][i], callback_data=category_callback.new(id_c=pre_list_category[0][i]))])

        choice_category = InlineKeyboardMarkup(inline_keyboard = [x for x in list_category])

        if list_category == []:
            await call.message.edit_text(f'🥺 Категории и товары в этом магазине отсутствуют')
        else:
            await call.message.edit_text(f'🔥 Ниже представлен список доступных категорий. Выбери любую, чтобы посмотреть находящиеся в ней товары!', reply_markup=choice_category)
    elif r[0][0] == 'item': # r[0][0] - идентификатор коллбэка (item, category, back_to_category и тд), r[0][1] - айди категории, r[1][1] - айди товара
        sql.execute(f"SELECT * FROM items WHERE id_item = {r[1][1]}")
        info_item = sql.fetchall()

        title = info_item[0][2]
        description = info_item[0][3]
        price = info_item[0][4]

        buy_real = CallbackData('buy_real', 'id_i')
        buy_ref = CallbackData('buy_ref', 'id_i')
        cb_data = CallbackData('back_to_items', 'id_c')

        try: # Если экземпляры есть
            sql.execute(f"SELECT * FROM instances WHERE id_item = {r[1][1]}")
            all_instances = sql.fetchall()

            random_instance = random.choice(all_instances)

            id_user = call.from_user.id

            sql_l.execute(f"SELECT ref_balance FROM users WHERE id_user = {id_user}")
            ref_balance = int(sql_l.fetchone()[0])

            sql.execute(f"SELECT price_item FROM items WHERE id_item = {r[1][1]}")
            price_item = int(sql.fetchone()[0])

            if ref_balance < price_item: # Если на реферальном счету недостаточно средств для покупки этого товара
                buy_kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='💳 Купить', callback_data=buy_real.new(id_i=r[1][1]))], [InlineKeyboardButton(text='◀️ Назад', callback_data=cb_data.new(id_c=r[0][1]))]])
                await call.message.edit_text(f'<b>{title}</b>\n\n{description}\n\nЦена: {price} руб.', reply_markup=buy_kb, parse_mode=types.ParseMode.HTML)
            elif ref_balance > price_item: # Если не реф. счет достаточно средств для покупки товара
                 buy_kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='💳 Купить за реальные деньги', callback_data=buy_real.new(id_i=r[1][1]))], [InlineKeyboardButton(text='👥 Купить за реферальные деньги', callback_data=buy_ref.new(id_i=r[1][1]))], [InlineKeyboardButton(text='◀️ Назад', callback_data=cb_data.new(id_c=r[0][1]))]])
                 await call.message.edit_text(f'<b>{title}</b>\n\n{description}\n\nЦена: {price} руб.', reply_markup=buy_kb, parse_mode=types.ParseMode.HTML)
        except IndexError:
            buy_kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='◀️ Назад', callback_data=cb_data.new(id_c=r[0][1]))]])
            await call.message.edit_text(f'<b>{title}</b>\n\n{description}\n\n⛔️ К сожалению, товар закончился', reply_markup=buy_kb, parse_mode=types.ParseMode.HTML)
    elif r[0][0] == 'back_to_items':
        id_category = r[0][1]

        item_callback = CallbackData('item', 'id_c', 'id_i')

        sql.execute(f"SELECT * FROM items WHERE id_category = {id_category}")
        list_items_from_db = sql.fetchall()

        pre_list_items = [[idi[1] for idi in list_items_from_db], [name[2] for name in list_items_from_db]]

        list_items = []

        for i in range(len(pre_list_items[0])):
            list_items.append([InlineKeyboardButton(text=pre_list_items[1][i], callback_data=item_callback.new(id_c=id_category, id_i=pre_list_items[0][i]))])

        cb_data = CallbackData('back_to_categories', 'id_s')

        list_items.append([InlineKeyboardButton(text='◀️ Назад', callback_data=cb_data.new(id_s=id_shop))])

        choice_item = InlineKeyboardMarkup(inline_keyboard = [x for x in list_items])

        if len(list_items) == 1:
            await call.message.edit_text(f'🥺 Товары в этой категории отсутствуют', reply_markup=choice_item)
        else:
            await call.message.edit_text(f'💥 Ниже список товаров выбранной вами категории', reply_markup=choice_item)
    elif r[0][0] == 'ref_link':
        await call.message.edit_text(f'👫 Ваша реферальная ссылка: t.me/{bot_name.username}?start={call.from_user.id}')
    elif r[0][0] == 'buy_real':
        sql.execute(f"SELECT price_item FROM items WHERE id_item = {r[0][1]}")
        price_item = int(sql.fetchone()[0])

        sql.execute(f"SELECT name_item FROM items WHERE id_item = {r[0][1]}")
        name_item = sql.fetchone()[0]

        bill = Bill()
        pay_url_qiwi = bill.to_invoice(bill.private, bill.bill_id, price_item)

        bill_ym = ym_api.Bill()
        pay_url_ym = bill_ym.to_invoice(name_item, price_item)

        method_pay__kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='🥝 QIWI Кошелек', url=pay_url_qiwi)], [InlineKeyboardButton(text='🧿 ЮMoney', url=pay_url_ym)]])

        await call.message.edit_text(f'💸 Выберите способ оплаты', reply_markup=method_pay__kb)

        async def check_bill():
            print('Началось')
            status = ''

            while status != 'PAID':
                status_qiwi = str
                status_ym = str

                status_qiwi = bill.status_invoice(bill.private, bill.bill_id)
                try:
                    status_ym = bill_ym.status_invoice()
                except IndexError:
                    pass

                if status_qiwi == 'PAID':
                    status = 'PAID'
                if status_ym == 'success':
                    status = 'PAID'

                await asyncio.sleep(2)

            print('while end')

            if status == 'PAID':
                sql.execute(f"SELECT id_category FROM items WHERE id_item = {r[0][1]}")
                id_category = sql.fetchone()[0]

                sql.execute(f"SELECT id_shop FROM categories WHERE id_category = {id_category}")
                id_shop = sql.fetchone()[0]

                sql.execute(f"SELECT id_user FROM shops WHERE id_shop = {id_shop}")
                id_user = sql.fetchone()[0]

                sql.execute(f"SELECT earn FROM users WHERE id_user = {id_user}")
                earn = sql.fetchone()[0] + price_item

                sql.execute(f"SELECT balance FROM users WHERE id_user = {id_user}")
                balance = sql.fetchone()[0] + price_item

                sql.execute(f"UPDATE users SET earn = {earn} WHERE id_user = {id_user}")
                db.commit()

                sql.execute(f"UPDATE users SET balance = {balance} WHERE id_user = {id_user}")
                db.commit()

                sql.execute(f"SELECT * FROM instances WHERE id_item = {r[0][1]}")
                all_instances = sql.fetchall()

                random_instance = random.choice(all_instances)

                if random_instance[3] == 0:
                    sql.execute(f"DELETE FROM instances WHERE id_instance = {random_instance[1]}")
                    db.commit()

                id_user = call.from_user.id

                sql_l.execute(f"SELECT item_bought FROM users WHERE id_user = {id_user}")
                item_bought = int(sql_l.fetchone()[0]) + 1

                sql_l.execute(f"UPDATE users SET item_bought = {item_bought} WHERE id_user = {id_user}")
                db_l.commit()

                sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
                ref_system = int(sql.fetchone()[0])

                if ref_system != 0:
                    sql_l.execute(f"SELECT id_ref FROM users WHERE id_user = {id_user}")
                    id_ref = sql_l.fetchone()[0]

                    if id_ref != 0:
                        ref_deduction = int(float('{:f}'.format(price_item / 100 * ref_system)))

                        sql_l.execute(f"SELECT * FROM users WHERE id_user = {id_ref}")
                        sqllfetchall = sql_l.fetchall()

                        earned_on_ref = sqllfetchall[0][3] + ref_deduction
                        ref_balance = sqllfetchall[0][4] + ref_deduction

                        sql_l.execute(f"UPDATE users SET earned_on_ref = {earned_on_ref} WHERE id_user = {id_ref}")
                        db_l.commit()

                        sql_l.execute(f"UPDATE users SET ref_balance = {ref_balance} WHERE id_user = {id_ref}")
                        db_l.commit()

                await call.message.edit_text(f'🎉 Спасибо за покупку!\n\n{random_instance[2]}')

        asyncio.create_task(check_bill())
    elif r[0][0] == 'buy_ref':
        sql.execute(f"SELECT id_category FROM items WHERE id_item = {r[0][1]}")
        id_category = sql.fetchone()[0]

        sql.execute(f"SELECT id_shop FROM categories WHERE id_category = {id_category}")
        id_shop = sql.fetchone()[0]

        sql.execute(f"SELECT id_user FROM shops WHERE id_shop = {id_shop}")
        id_user = sql.fetchone()[0]

        sql.execute(f"SELECT earn FROM users WHERE id_user = {id_user}")
        earn = sql.fetchone()[0] + price_item

        sql.execute(f"SELECT balance FROM users WHERE id_user = {id_user}")
        balance = sql.fetchone()[0] + price_item

        sql.execute(f"UPDATE users SET earn = {earn} WHERE id_user = {id_user}")
        db.commit()

        sql.execute(f"UPDATE users SET balance = {balance} WHERE id_user = {id_user}")
        db.commit()

        sql.execute(f"SELECT * FROM instances WHERE id_item = {r[0][1]}")
        all_instances = sql.fetchall()

        random_instance = random.choice(all_instances)

        if random_instance[3] == 0:
            sql.execute(f"DELETE FROM instances WHERE id_instance = {random_instance[1]}")
            db.commit()

        id_user = call.from_user.id

        sql_l.execute(f"SELECT ref_balance FROM users WHERE id_user = {id_user}")
        ref_balance = int(sql_l.fetchone()[0])

        sql.execute(f"SELECT price_item FROM items WHERE id_item = {r[0][1]}")
        price_item = int(sql.fetchone()[0])

        ref_balance = ref_balance - price_item

        sql_l.execute(f"UPDATE users SET ref_balance = {ref_balance} WHERE id_user = {id_user}")
        db_l.commit()

        sql_l.execute(f"SELECT item_bought FROM users WHERE id_user = {id_user}")
        item_bought = int(sql_l.fetchone()[0]) + 1

        sql_l.execute(f"UPDATE users SET item_bought = {item_bought} WHERE id_user = {id_user}")
        db_l.commit()

        sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
        ref_system = int(sql.fetchone()[0])

        if ref_system != 0:
            sql_l.execute(f"SELECT id_ref FROM users WHERE id_user = {id_user}")
            id_ref = sql_l.fetchone()[0]

            if id_ref != 0:
                sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
                ref_system = int(sql.fetchone()[0])

                ref_deduction = int(float('{:f}'.format(price_item / 100 * ref_system)))

                sql_l.execute(f"SELECT * FROM users WHERE id_user = {id_ref}")
                sqllfetchall = sql_l.fetchall()
                print(sqllfetchall)
                earned_on_ref = sqllfetchall[0][3] + ref_deduction
                ref_balance = sqllfetchall[0][4] + ref_deduction

                sql_l.execute(f"UPDATE users SET earned_on_ref = {earned_on_ref} WHERE id_user = {id_ref}")
                db_l.commit()

                sql_l.execute(f"UPDATE users SET ref_balance = {ref_balance} WHERE id_user = {id_ref}")
                db_l.commit()

        await call.message.edit_text(f'🎉 Спасибо за покупку!\n\n{random_instance[2]}')
    elif r[0][0] == 'method_pay':
        method = r
        print(method)

async def on_startup(_):
    sql_l.execute(f"SELECT id_user FROM users")
    all_users = sql_l.fetchall()
    print(f'All users: {all_users}')
    for user in all_users:
        print(f'User: {user}')
        await bot.send_message(user[0], f'🔄 Магазин был обновлен! Введите команду /start для перезагрузки магазина', reply_markup=ReplyKeyboardRemove())
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
