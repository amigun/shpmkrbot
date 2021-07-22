# Импортируем нужные библиотеки
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from threading import Thread
import sqlite3, os, sys, time, re, random

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

# Функция ожидания остановки
def listening():
    is_quit = 0 # По умолчанию, выходить не надо

    while is_quit != 1: # Пока is_quit не станет 1 (пока не надо будет выйти)
        sql.execute(f"SELECT is_del FROM is_dp WHERE id_shop = {id_shop}")
        is_del = sql.fetchone()[0]

        sql.execute(f"SELECT is_pause FROM is_dp WHERE id_shop = {id_shop}")
        is_pause = sql.fetchone()[0]

        if is_del == 1 or is_pause == 1:
            is_quit = 1

        time.sleep(10)

    os._exit(0) # Завершить работу магазина

# Запускаю отдельный поток
thread = Thread(target=listening)
thread.start()

# Создаем глобальные переменные
ref_system = 0
support = '-'
coupon = '-'

# Приветственное сообщение
@dp.message_handler(commands=['start'], state='*')
async def process_start_command(msg: types.Message):
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

    await bot.send_message(msg.from_user.id, f'👋Добро пожаловать в {name_shop}, {msg.from_user.first_name}!', reply_markup=ReplyKeyboardRemove())
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
            await bot.send_message(msg.from_user.id, f'Пользователь: {msg.from_user.first_name}\nКуплено товаров: {user_info[1]}\nКоличество рефералов: {user_info[2]}\nЗаработано на рефералах: {user_info[3]}\nРеферальный баланс: {user_info[4]}')
        else:
            await bot.send_message(msg.from_user.id, f'Пользователь: {msg.from_user.first_name}\nКуплено товаров: {user_info[1]}')
    elif msg.text == '👥 Реферальная система':
        sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
        ref_percent = sql.fetchone()[0]

        ref_link = CallbackData('ref_link', 'id_s')

        get_ref_link = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='🔶 Получить реферальную ссылку', callback_data=ref_link.new(id_s=id_shop))]])

        await bot.send_message(msg.from_user.id, f'🔺 В нашем магазине существует реферальная система! Привлекай клиентов в наш магазин и получай {ref_percent}% с каждой их покупки на свой реферальный баланс, который можешь потратить на внутренние покупки', reply_markup=get_ref_link)
    elif msg.text == '🔧 Тех. поддержка':
        sql.execute(f"SELECT support FROM shops WHERE id_shop = {id_shop}")

        await bot.send_message(msg.from_user.id, sql.fetchone()[0])
    elif msg.text == '🎟  Актуальный купон':
        sql.execute(f"SELECT actual_coupon FROM shops WHERE id_shop = {id_shop}")

        await bot.send_message(msg.from_user.id, sql.fetchone()[0])

@dp.callback_query_handler(lambda callback_query: True)
async def inline_button(call: types.CallbackQuery):
    global id_shop
    await call.answer(cache_time=2)
    r = re.findall(r'([a-z_]*):([0-9]*)', call.data)

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
            print(id_user)

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
        await call.message.edit_text(f'Ваша реферальная ссылка: t.me/{bot_name.username}?start={call.from_user.id}')
    elif r[0][0] == 'buy':
        sql.execute(f"SELECT id_user FROM shops WHERE id_shop = {id_shop}")
        id_user = sql.fetchone()[0]

        sql_l.execute(f"SELECT ref_balance FROM users WHERE id_user = {id_user}")
        ref_balance = int(sql_l.fetchone()[0])

        sql.execute(f"SELECT price_item FROM items WHERE id_item = {r[0][1]}")
        price_item = int(sql.fetchone()[0])

        if ref_balance < price_item:
            you_buy_this_item = True

            if you_buy_this_item:
                sql.execute(f"SELECT * FROM instances WHERE id_item = {r[0][1]}")
                all_instances = sql.fetchall()

                random_instance = random.choice(all_instances)

                if random_instance[3] == 0:
                    sql.execute(f"DELETE FROM instances WHERE id_instance = {random_instance[1]}")
                    db.commit()

                #sql.execute(f"SELECT id_user FROM shops WHERE id_shop = {id_shop}")
                #id_user = sql.fetchone()[0]
                id_user = call.message.from_user.id

                sql_l.execute(f"SELECT ref_balance FROM users WHERE id_user = {id_user}")
                ref_balance = int(sql_l.fetchone()[0])

                sql.execute(f"SELECT price_item FROM items WHERE id_item = {r[0][1]}")
                price_item = int(sql.fetchone()[0])

                new_ref_balance = ref_balance - price_item

                sql_l.execute(f"UPDATE users SET ref_balance = {new_ref_balance} WHERE id_user = {id_user}")

                sql_l.execute(f"SELECT item_bought FROM users WHERE id_user = {id_user}")
                item_bought = int(sql_l.fetchone()[0])

                item_bought += 1

                sql_l.execute(f"UPDATE users SET item_bought = {item_bought} WHERE id_user = {id_user}")

                sql_l.execute(f"SELECT id_ref FROM users WHERE id_user = {id_user}")
                id_ref = sql_l.fetchone()[0]

                db.commit()

                if id_ref != 0:
                    sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
                    ref_system = int(sql.fetchone()[0])

                    ref_deduction = price_item - (price_item / 100 * ref_system)

                    sql_l.execute(f"SELECT * FROM users WHERE id_user = {id_ref}")
                    earned_on_ref = sql.fetchall()

                await call.message.edit_text(f'🎉 Спасибо за покупку!\n\n{random_instance[2]}')
        elif ref_balance > price_item:
            buy_callback = CallbackData('buy', 'id_i')
            buy_with_real_money_callback = CallbackData('buy_real', 'id_i')
            buy_with_ref_balance_callback = CallbackData('buy_ref', 'id_i')
            cb_data = CallbackData('back_to_items', 'id_c')

            sql.execute(f"SELECT id_category FROM items WHERE id_item = {r[0][1]}")
            id_category = sql.fetchone()[0]

            buy_kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='💳 Купить за реальные деньги', callback_data=buy_with_real_money_callback.new(id_i=r[0][1]))], [InlineKeyboardButton(text='👥 Купить за реферальные деньги', callback_data=buy_with_ref_balance_callback.new(id_i=r[0][1]))], [InlineKeyboardButton(text='◀️ Назад', callback_data=cb_data.new(id_c=id_category))]])

            await call.message.edit_text(f'На вашем реферальном балансе достаточно денег, чтобы оплатить товар. Использовать реферальный баланс или купить за реальные деньги?', reply_markup=buy_kb)
    elif r[0][0] == 'buy_real':
        you_buy_this_item = True

        if you_buy_this_item:
            sql.execute(f"SELECT * FROM instances WHERE id_item = {r[0][1]}")
            all_instances = sql.fetchall()

            random_instance = random.choice(all_instances)

            if random_instance[3] == 0:
                sql.execute(f"DELETE FROM instances WHERE id_instance = {random_instance[1]}")
                db.commit()

            await call.message.edit_text(f'🎉 Спасибо за покупку!\n\n{random_instance[2]}')
    elif r[0][0] == 'buy_ref':
        sql.execute(f"SELECT * FROM instances WHERE id_item = {r[0][1]}")
        all_instances = sql.fetchall()

        random_instance = random.choice(all_instances)

        if random_instance[3] == 0:
            sql.execute(f"DELETE FROM instances WHERE id_instance = {random_instance[1]}")
            db.commit()

        sql.execute(f"SELECT id_user FROM shops WHERE id_shop = {id_shop}")
        id_user = sql.fetchone()[0]

        sql_l.execute(f"SELECT ref_balance FROM users WHERE id_user = {id_user}")
        ref_balance = int(sql_l.fetchone()[0])

        sql.execute(f"SELECT price_item FROM items WHERE id_item = {r[0][1]}")
        price_item = int(sql.fetchone()[0])

        new_ref_balance = ref_balance - price_item

        sql_l.execute(f"UPDATE users SET ref_balance = {new_ref_balance} WHERE id_user = {id_user}")

        sql_l.execute(f"SELECT item_bought FROM users WHERE id_user = {id_user}")
        item_bought = int(sql_l.fetchone()[0])

        item_bought += 1

        sql_l.execute(f"UPDATE users SET item_bought = {item_bought} WHERE id_user = {id_user}")

        sql_l.execute(f"SELECT id_ref FROM users WHERE id_user = {id_user}")
        id_ref = sql_l.fetchone()[0]

        db.commit()

        print(f'После коммита, перед ифом')

        if id_ref != 0:
            print(f'В ифе')
            sql.execute(f"SELECT ref_system FROM shops WHERE id_shop = {id_shop}")
            ref_system = int(sql.fetchone()[0])

            ref_deduction = price_item - (price_item / 100 * ref_system)

            sql_l.execute(f"SELECT * FROM users WHERE id_user = {id_ref}")
            earned_on_ref = sql.fetchall()
            print(f'earned_on_ref::::::: {earned_on_ref}')
        print(f'После ифа')

        await call.message.edit_text(f'🎉 Спасибо за покупку!\n\n{random_instance[2]}')

if __name__ == '__main__':
    executor.start_polling(dp)
