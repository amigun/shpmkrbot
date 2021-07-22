# Импортируем нужные библиотеки
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from threading import Thread
from loguru import logger as log
from dotenv import load_dotenv
import sqlite3
import re
import shutil
import os
import subprocess
import asyncio
import time

# Включаем логирование
log.add('logfiles/logging.log', format='{time} {message}', rotation='1 week', compression='zip')
log.info('Launching the bot. Importing libraries and creating a log file')

# Создаем базу данных
db = sqlite3.connect('database.db', check_same_thread = False)
sql = db.cursor()
log.info('Connecting to the database')

# Импортируем и кнопки
import buttons

# Импортируем переменные окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")

# Инициализируем бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Создаем функцию для запуска бота
def start_bot(path, id_user, id_shop):
    os.system(f'python {path} {id_user} {id_shop}')
    print('Поток закрыт')
    log.info('Thread is closed')

# Создаем класс для машины состояний
class menu(StatesGroup):
    mainmenu = State()
    my_shops = State()
    account = State()

# Когда создается новый магазин
class newbot(StatesGroup):
    name_shop = State()
    token = State()

# Управление магазином
class control_panel(StatesGroup):
    wait_event = State()
    post_category = State()
    wait_name_category = State()
    categories_event = State()
    wait_new_name_category = State()
    wait_catogory_for_item = State()
    wait_name_item = State()
    wait_description_item = State()
    wait_price_item = State()
    wait_category_for_see_item = State()
    item_event = State()
    wait_new_name_item = State()
    wait_new_description_item = State()
    wait_new_price_item = State()
    wait_support_message = State()
    wait_coupon_message = State()
    wait_ref = State()
    wait_new_name_for_shop = State()
    wait_name_instance = State()
    wait_type_of_instance = State()
    wait_instance = State()
    wait_event_instance = State()
    wait_new_name_instance = State()
    wait_new_type_instance = State()
    wait_payments = State()
    wait_qiwi_requisites = State()
    wait_card_requisites = State()
    wait_yoomoney_requisites = State()
    wait_text_newsletter = State()

selected_shop = -1
selected_category = -1
selected_item = -1
selected_instance = -1

# Приветственное сообщение
@dp.message_handler(commands=['start'], state='*')
async def process_start_command(msg: types.Message):
    await bot.send_message(msg.from_user.id, f'👋Добро пожаловать в shopmaker, {msg.from_user.first_name}!', reply_markup=buttons.mainmenu__kb)

    log.info(f'The {msg.from_user.id} entered the /start command')

    sql.execute(f"SELECT id_user FROM users WHERE id_user = '{msg.from_user.id}'")
    if sql.fetchone() is None:
        sql.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (msg.from_user.id, 0, 0, 0, 0))
        db.commit()

        log.info(f'A new row has been created in the "users" table')

    await menu.mainmenu.set()

@dp.message_handler(commands=['quit'], state='*')
async def process_start_command(msg: types.Message):
    log.info('The program was stopped by the /quit command')
    quit()

@dp.message_handler(commands=['admin'], state='*')
async def login_admin(msg: types.Message):
    password = msg.get_args()
    if password == 'uPiAmynY21ywk':
        sql.execute(f"UPDATE users SET admin = 1 WHERE id_user = {msg.from_user.id}")
        db.commit()

        log.info(f'{msg.from_user.id} became an admin')
        await bot.send_message(msg.from_user.id, f'Вы теперь админ!')

@dp.message_handler(commands=['newsletter'], state='*')
async def newsletter(msg: types.Message):
    print(msg.text[12:])

"""
# Функция для проверки отправки рассылки
async def check_newsletter():
    while True:
        sql.execute(f"SELECT newsletter FROM shops WHERE newsletter = 0")
        all_shops = sql.fetchall()
        if all_shops == []:
            with open('newsletter/newsletter.txt', 'w') as f:
                f.write('')

            sql.execute(f"UPDATE shops SET newsletter = 0")
            db.commit()
        await asyncio.sleep(1)

# Создание потока
loop = asyncio.get_event_loop()
loop.create_task(check_newsletter())
"""

# Отслеживание нажатий на кнопки из главного меню
@dp.message_handler(state=menu.mainmenu)
async def echo_message(msg: types.Message):
    if msg.text == '🛒 Мои магазины':
        log.info(f'{msg.from_user.id} went to the list of shops')

        my_shops__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        sql.execute(f"SELECT name_shop FROM shops WHERE id_user = '{msg.from_user.id}'")

        all_shops = sql.fetchall()

        for name in all_shops:
            my_shops__kb.add(KeyboardButton(str(name[0])))

        my_shops__button_1 = KeyboardButton('🤖Создать новый')
        my_shops__button_2 = KeyboardButton('◀ Назад')

        my_shops__kb.add(my_shops__button_1, my_shops__button_2)

        if len(all_shops) != 0:
            await bot.send_message(msg.from_user.id, '🛒 Ниже ваш список магазинов. Выберите любой, чтобы посмотреть информацию о нем или редактировать', reply_markup=my_shops__kb)
        else:
            await bot.send_message(msg.from_user.id, '🤖 У вас ещё нет магазина, создайте новый', reply_markup=my_shops__kb)
        await menu.my_shops.set()
    elif msg.text == '🔓 Личный кабинет':
        log.info(f'{msg.from_user.id} logged into "my personal account"')

        sql.execute(f"SELECT * FROM users WHERE id_user = '{msg.from_user.id}'")
        string_db = sql.fetchone()

        await bot.send_message(msg.from_user.id, f'👤 Пользователь: {msg.from_user.first_name}\n🏪 Количество магазинов: {string_db[1]}\n💰 Заработано всего: {string_db[2]}\n💸 Баланс: {string_db[3]}', reply_markup=buttons.account__kb)
        await menu.account.set()

# Если нажата кнопка Мои магазины
@dp.message_handler(state=menu.my_shops)
async def command_my_shops(msg: types.Message):
    if msg.text == '◀ Назад':
        log.info(f'{msg.from_user.id} returned to the main menu from the list of shops')

        await bot.send_message(msg.from_user.id, f'📌 Вы в главном меню!', reply_markup=buttons.mainmenu__kb)
        await menu.mainmenu.set()
    elif msg.text == '🤖Создать новый':
        log.info(f'{msg.from_user.id} clicked the button to create a new shop')

        await bot.send_message(msg.from_user.id, f'▶️ Введите название магазина:', reply_markup=ReplyKeyboardRemove())
        await newbot.name_shop.set()
    else:
        sql.execute(f"SELECT name_shop FROM shops WHERE id_user = '{msg.from_user.id}'")

        list_names_shops = []
        for name in sql.fetchall():
            list_names_shops.append(name[0])

        if msg.text in list_names_shops:
            sql.execute(f"SELECT id_shop FROM shops WHERE (id_user = '{msg.from_user.id}' and name_shop = '{msg.text}')")

            global selected_shop
            selected_shop = sql.fetchall()[0][0]

            await bot.send_message(msg.from_user.id, f'⚙ Панель управления магазином «{msg.text}». Выберите действие', reply_markup=buttons.control_panel__kb)
            log.info(f'{msg.from_user.id} went to the shop "{msg.text}"')

            await control_panel.wait_event.set()
        else:
            pass

# Ожидание введения названия магазина и переход на ожидание токена
@dp.message_handler(state=newbot.name_shop)
async def get_name_newbot(msg: types.Message, state: FSMContext):
    log.info(f'{msg.from_user.id} entered the name of the new shop: "{msg.text}"')

    await state.update_data(name_shop=msg.text)
    await bot.send_message(msg.from_user.id, f'🐝 Перейдите в @BotFather, создайте бота и пришлите сюда полученный token:')
    await newbot.token.set()

# Ожидание введения токена бота
@dp.message_handler(state=newbot.token)
async def get_token(msg: types.Message, state: FSMContext):
    sql.execute(f"SELECT token_bot FROM shops WHERE token_bot = '{msg.text}'")
    r = re.search(r'[0-9]*:[a-zA-z0-9]*', msg.text)

    if sql.fetchall() != []:
        await bot.send_message(msg.from_user.id, f'🟡 Магазин с таким токеном уже существует!')
    elif r == None:
        await bot.send_message(msg.from_user.id, f'🟡 Кажется, это не похоже на токен. Попробуйте снова')
    elif r != None:
        log.info(f'{msg.from_user.id} introduced a new shop token: "{msg.text}"')

        try:
            sql.execute(f"SELECT * FROM shops WHERE ROWID IN (SELECT max(ROWID) FROM shops)")
            count_str = sql.fetchone()[1] + 1
        except TypeError:
            count_str = 0

        user_data = await state.get_data()

        sql.execute(f"SELECT * FROM shops WHERE id_shop = {count_str}")
        if sql.fetchone() is None:
            sql.execute("INSERT INTO shops VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (int(msg.from_user.id), int(count_str), str(user_data['name_shop']), str(msg.text), str('-'), str('-'), int(0), int(0)))
            db.commit()

            log.info(f'Shop {msg.from_user.id}_{count_str} has been created. A new row has been created in the "shops" table')

        sql.execute(f"SELECT count_shops FROM users WHERE id_user = '{msg.from_user.id}'")
        count_shops = int(sql.fetchone()[0]) + 1

        sql.execute(f"UPDATE users SET count_shops = {count_shops} WHERE id_user = {msg.from_user.id}")
        db.commit()

        log.info(f'The number of shop was changed for user {msg.from_user.id}')

        sql.execute(f"SELECT name_shop FROM shops WHERE id_user = '{msg.from_user.id}'")

        list_shops__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name_shop in sql.fetchall():
            list_shops__kb.add(KeyboardButton(name_shop[0]))

        list_shops__button_1 = KeyboardButton('🤖Создать новый')
        list_shops__button_2 = KeyboardButton('◀ Назад')

        list_shops__kb.add(list_shops__button_1, list_shops__button_2)

        shutil.copytree('shops/template', f'shops/{msg.from_user.id}_{count_str}')

        log.info(f'The shop {msg.from_user.id}_{count_str} folder was created')

        path = f'shops/{msg.from_user.id}_{count_str}/main.py'
        new_bot = Thread(target=start_bot, args=(path, msg.from_user.id, count_str))
        new_bot.start()

        f = open(f'newsletter/newsletter{count_str}.txt', 'w')
        f.write('\n')
        f.close()

        log.info(f'Store {msg.from_user.id}_{count_str} launched')

        sql.execute(f"SELECT * FROM is_dp WHERE id_shop = {count_str}")
        if sql.fetchone() is None:
            sql.execute("INSERT INTO is_dp VALUES (?, ?, ?)", (int(count_str), 0, 0))
            db.commit()
        else:
            pass

        await bot.send_message(msg.from_user.id, f'🔥 Ваш магазин создан! Выберите его в списке ниже, чтобы настроить', reply_markup=list_shops__kb)

        await menu.my_shops.set()

# Когда нажата кнопка редактирования магазина
@dp.message_handler(state=control_panel.wait_event)
async def edit_shop(msg: types.Message):
    global selected_shop

    if msg.text == '◀ Назад':
        log.info(f'{msg.from_user.id} returned to the list of shops')

        sql.execute(f"SELECT name_shop FROM shops WHERE id_user = '{msg.from_user.id}'")

        list_shops__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name_shop in sql.fetchall():
            list_shops__kb.add(KeyboardButton(name_shop[0]))

        list_shops__button_1 = KeyboardButton('🤖Создать новый')
        list_shops__button_2 = KeyboardButton('◀ Назад')

        list_shops__kb.add(list_shops__button_1, list_shops__button_2)

        await bot.send_message(msg.from_user.id, f'🛒 Ниже ваш список магазинов. Выберите любой, чтобы посмотреть информацию о нем или редактировать', reply_markup=list_shops__kb)

        await menu.my_shops.set()
    elif msg.text == '📦 Категории':
        log.info(f'{msg.from_user.id} entered the list of categories')

        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
        list_categories = sql.fetchall()

        list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_categories:
            list_categories__kb.add(KeyboardButton(name[0]))

        list_categories__button_1 = KeyboardButton('🤖Создать новую')
        list_categories__button_2 = KeyboardButton('◀ Назад')

        list_categories__kb.add(list_categories__button_1, list_categories__button_2)

        if len(list_categories) != 0:
            await bot.send_message(msg.from_user.id, f'🟡 Ниже список ваших категорий. Выберите любую, чтобы изменить ее название или удалить', reply_markup=list_categories__kb)
        else:
            await bot.send_message(msg.from_user.id, f'📂 У вас еще нет категории, создайте новую', reply_markup=list_categories__kb)
        await control_panel.post_category.set()
    elif msg.text == '🎈 Товары':
        log.info(f'{msg.from_user.id} entered the list of items')

        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
        list_categories = sql.fetchall()

        list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_categories:
            list_categories__kb.add(KeyboardButton(name[0]))

        list_categories__button_1 = KeyboardButton('◀ Назад')

        list_categories__kb.add(list_categories__button_1)

        if len(list_categories) != 0:
            await bot.send_message(msg.from_user.id, f'👆 Выберите категорию, чтобы посмотреть все находящиеся в ней товары', reply_markup=list_categories__kb)
        else:
            await bot.send_message(msg.from_user.id, f'❗️ Прежде чем создавать товары, нужно создать категорию. Вернитесь в меню, и создайте категорию', reply_markup=list_categories__kb)

        await control_panel.wait_category_for_see_item.set()
    elif msg.text == '⚙ Тех. поддержка':
        await bot.send_message(msg.from_user.id, f'🕹 Добавьте текст и контакты, которые увидит клиент, если ему понадобится помощь')
        await control_panel.wait_support_message.set()
    elif msg.text == '📃 Актуальный купон':
        await bot.send_message(msg.from_user.id, f'▶️ Введите текст актуального купона')
        await control_panel.wait_coupon_message.set()
    elif msg.text == '👥 Реферальная система':
        await bot.send_message(msg.from_user.id, f'▶️ Введите процент, который будет получать рефовод за каждую покупку его рефералов, либо введите 0 чтобы отключить реферальную систему (по умолчанию 0)')
        await control_panel.wait_ref.set()
    elif msg.text == '❌ Удалить магазин':
        shutil.rmtree(f'shops/{msg.from_user.id}_{selected_shop}')

        sql.execute(f"DELETE FROM shops WHERE id_shop = {selected_shop}")
        sql.execute(f"DELETE FROM is_dp WHERE id_shop = {selected_shop}")

        sql.execute(f"SELECT id_category FROM categories WHERE id_shop = {selected_shop}")
        id_categories = []
        for id in sql.fetchall():
            id_categories.append(id[0])

        id_items = []
        for id in id_categories:
            sql.execute(f"SELECT id_item FROM items WHERE id_category = {id}")
            for ids in sql.fetchall():
                id_items.append(ids[0])

        for id in id_categories:
            sql.execute(f"DELETE FROM categories WHERE id_category = {id}")

        for id in id_items:
            sql.execute(f"DELETE FROM instances WHERE id_item = {id}")

        for id in id_items:
            sql.execute(f"DELETE FROM items WHERE id_item = {id}")

        sql.execute(f"SELECT count_shops FROM users WHERE id_user = '{msg.from_user.id}'")
        count_shops = int(sql.fetchone()[0]) - 1

        sql.execute(f"UPDATE users SET count_shops = {count_shops} WHERE id_user = {msg.from_user.id}")

        db.commit()

        sql.execute(f"SELECT name_shop FROM shops WHERE id_user = '{msg.from_user.id}'")

        list_shops__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name_shop in sql.fetchall():
            list_shops__kb.add(KeyboardButton(name_shop[0]))

        list_shops__button_1 = KeyboardButton('🤖Создать новый')
        list_shops__button_2 = KeyboardButton('◀ Назад')

        list_shops__kb.add(list_shops__button_1, list_shops__button_2)

        sql.execute(f"UPDATE is_dp SET is_del = {1} WHERE id_shop = {selected_shop}")
        db.commit()

        log.info(f'{msg.from_user.id} deleted the shop "{msg.from_user.id}_{selected_shop}"')

        await bot.send_message(msg.from_user.id, f'🗑 Магазин удален. Ниже ваш список магазинов. Выберите любой, чтобы посмотреть информацию о нем или редактировать', reply_markup=list_shops__kb)

        await menu.my_shops.set()
    elif msg.text == '✏️ Изменить название':
        await bot.send_message(msg.from_user.id, f'▶️ Введите новое название')
        await control_panel.wait_new_name_for_shop.set()
    elif msg.text == '⏯ Запустить/остановить':
        sql.execute(f"SELECT is_pause FROM is_dp WHERE id_shop = {selected_shop}")
        is_pause = sql.fetchone()[0]
        if is_pause == 0:
            sql.execute(f"UPDATE is_dp SET is_pause = {1} WHERE id_shop = {selected_shop}")
            db.commit()

            log.info(f'{msg.from_user.id} stopped the shop "{msg.from_user.id}_{selected_shop}"')

            await bot.send_message(msg.from_user.id, f'▶️ Ваш магазин остановлен!')
        elif is_pause == 1:
            path = f'shops/{msg.from_user.id}_{selected_shop}/main.py'
            new_bot = Thread(target=start_bot, args=(path, msg.from_user.id, selected_shop))
            new_bot.start()

            sql.execute(f"UPDATE is_dp SET is_pause = {0} WHERE id_shop = {selected_shop}")
            db.commit()

            log.info(f'{msg.from_user.id} launched a shop "{msg.from_user.id}_{selected_shop}"')

            await bot.send_message(msg.from_user.id, f'⏸ Ваш магазин запущен!')
    elif msg.text == '✉️ Рассылка':
        await bot.send_message(msg.from_user.id, f'📭 Введите текст для рассылки, которую получат все ваши клиенты')
        await control_panel.wait_text_newsletter.set()

# Ожидание текста для рассылки
@dp.message_handler(state=control_panel.wait_text_newsletter)
async def wait_text_newsletter(msg: types.Message):
    global selected_shop

    with open(f'newsletter/newsletter{selected_shop}.txt', 'w') as f:
        f.write(msg.text)

    log.info(f'{msg.from_user.id} started a newsletter with the text: {msg.text}')

    await bot.send_message(msg.from_user.id, f'📤 Рассылка началась!')
    await control_panel.wait_event.set()

# Ожидание ввода нового названия для магазина
@dp.message_handler(state=control_panel.wait_new_name_for_shop)
async def wait_new_name_for_shop(msg: types.Message):
    global selected_shop

    sql.execute(f"UPDATE shops SET name_shop = '{msg.text}' WHERE id_shop = {selected_shop}")
    db.commit()

    log.info(f'{msg.from_user.id} changed the name of the store "{msg.from_user.id}_{selected_shop}" to "{msg.text}"')

    await bot.send_message(msg.from_user.id, f'✅ Название изменено!')
    await control_panel.wait_event.set()

# Ожидание ввода сообщения для тех. поддержки
@dp.message_handler(state=control_panel.wait_support_message)
async def wait_support_message(msg: types.Message):
    global selected_shop

    sql.execute(f"UPDATE shops SET support = '{msg.text}' WHERE id_shop = {selected_shop}")
    db.commit()

    log.info(f'{msg.from_user.id} changed the support message')

    await bot.send_message(msg.from_user.id, f'💾 Сообщение сохранено!')
    await control_panel.wait_event.set()

# Ожидание ввода сообщения для актуального купона
@dp.message_handler(state=control_panel.wait_coupon_message)
async def wait_coupon_message(msg: types.Message):
    global selected_shop

    sql.execute(f"UPDATE shops SET actual_coupon = '{msg.text}' WHERE id_shop = {selected_shop}")
    db.commit()

    log.info(f'{msg.from_user.id} changed the actual coupon message')

    await bot.send_message(msg.from_user.id, f'💾 Сообщение сохранено!')
    await control_panel.wait_event.set()

# Ожидание ввода процента реферальной системы
@dp.message_handler(state=control_panel.wait_ref)
async def wait_ref(msg: types.Message):
    global selected_shop

    if msg.text == '0':
        sql.execute(f"UPDATE shops SET ref_system = '{msg.text}' WHERE id_shop = {selected_shop}")
        db.commit()

        log.info(f'{msg.from_user.id} disabled the referral system')

        await bot.send_message(msg.from_user.id, f'🚫 Реферальная система отключена!')
        await control_panel.wait_event.set()
    else:
        try:
            if int(msg.text) > 100 or int(msg.text) < 0:
                await bot.send_message(msg.from_user.id, f'❗️ Процент реферальной системы не может быть меньше 0 и больше 100! Попробуйте снова')
            else:
                sql.execute(f"UPDATE shops SET ref_system = '{msg.text}' WHERE id_shop = {selected_shop}")
                db.commit()

                log.info(f'{msg.from_user.id} changed the percentage of the referral system by {msg.text}%')

                await bot.send_message(msg.from_user.id, f'Процент реферальной системы изменен!')
                await control_panel.wait_event.set()
        except ValueError:
            await bot.send_message(msg.from_user.id, f'🟡 Кажется, это не число, а процент реферальной системы может быть только в виде числа. Попробуйте снова')

# Ждем ввода категории, товары в которой надо посмотреть
@dp.message_handler(state=control_panel.wait_category_for_see_item)
async def wait_category_for_see_item(msg: types.Message):
    global selected_shop

    if msg.text == '◀ Назад':
        sql.execute(f"SELECT name_shop FROM shops WHERE id_shop = {selected_shop}")

        log.info(f'{msg.from_user.id} returned to the store\'s control panel')

        await bot.send_message(msg.from_user.id, f'⚙ Панель управления магазином «{sql.fetchone()[0]}». Выберите действие', reply_markup=buttons.control_panel__kb)
        await control_panel.wait_event.set()
    else:
        global selected_category
        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")

        list_categories_shops = []
        for name in sql.fetchall():
            list_categories_shops.append(name[0])

        if msg.text in list_categories_shops:
            sql.execute(f"SELECT id_category FROM categories WHERE (name_category = '{msg.text}' and id_shop = '{selected_shop}')")
            selected_category = sql.fetchone()[0]

            sql.execute(f"SELECT name_item FROM items WHERE id_category = {selected_category}")
            list_item = sql.fetchall()

            list_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

            for name in list_item:
                list_item__kb.add(KeyboardButton(name[0]))

            list_item__button_1 = KeyboardButton('🤖Добавить новый')
            list_item__button_2 = KeyboardButton('◀ Назад')

            list_item__kb.add(list_item__button_1, list_item__button_2)

            if len(list_item) != 0:
                log.info(f'{msg.from_user.id} entered the list of products of the category')

                await bot.send_message(msg.from_user.id, f'⬇️ Внизу список товаров в этой категории. Нажмите на любой, чтобы редактировать или удалить', reply_markup=list_item__kb)
            else:
                await bot.send_message(msg.from_user.id, f'❗️ У вас еще нету ни одного товара, создайте новый!', reply_markup=list_item__kb)

            await control_panel.wait_catogory_for_item.set()

# Когда ждем категорию в которую создаем товар
@dp.message_handler(state=control_panel.wait_catogory_for_item)
async def wait_catogory_for_item(msg: types.Message):
    global selected_shop
    global selected_category
    global selected_item

    if msg.text == '◀ Назад':
        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
        list_categories = sql.fetchall()

        list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_categories:
            list_categories__kb.add(KeyboardButton(name[0]))

        list_categories__button_1 = KeyboardButton('◀ Назад')

        list_categories__kb.add(list_categories__button_1)

        log.info(f'{msg.from_user.id} returned to the list of categories in which you need to create a product')

        if len(list_categories) != 0:
            await bot.send_message(msg.from_user.id, f'👆 Выберите категорию, чтобы посмотреть все находящиеся в ней товары', reply_markup=list_categories__kb)
        else:
            await bot.send_message(msg.from_user.id, f'❗️ Прежде чем создавать товары, нужно создать категорию. Вернитесь в меню, и создайте категорию', reply_markup=list_categories__kb)

        await control_panel.wait_category_for_see_item.set()
    elif msg.text == '🤖Добавить новый':
        log.info(f'{msg.from_user.id} clicked on the button to create a new product')

        await bot.send_message(msg.from_user.id, f'▶️ Введите название товара', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_name_item.set()
    else:
        log.info(f'{msg.from_user.id} went to the product control panel')

        sql.execute(f"SELECT id_item FROM items WHERE (id_category = {selected_category} and name_item = '{msg.text}')")
        selected_item = sql.fetchone()[0]

        sql.execute(f"SELECT name_item FROM items WHERE id_item = {selected_item}")
        name_item = sql.fetchone()[0]

        sql.execute(f"SELECT description_item FROM items WHERE id_item = {selected_item}")
        description_item = sql.fetchone()[0]

        sql.execute(f"SELECT price_item FROM items WHERE id_item = {selected_item}")
        price_item = sql.fetchone()[0]

        cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
        cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
        cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
        cp_item__button_4 = KeyboardButton('❌ Удалить товар')
        cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
        cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
        cp_item__button_7 = KeyboardButton('◀ Назад')

        cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

        await bot.send_message(msg.from_user.id, f'💢 Название товара: {name_item}\n\n⭕️ Описание товара: {description_item}\n\n💲 Цена товара: {price_item}\n\nВыберите действие над товаром', reply_markup=cp_item__kb)
        await control_panel.item_event.set()

# Ожидаем действие над товаром
@dp.message_handler(state=control_panel.item_event)
async def item_event(msg: types.Message):
    global selected_item
    global selected_instance

    if msg.text == '✏️ Редактировать название':
        await bot.send_message(msg.from_user.id, f'▶️ Введите новое название для товара', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_new_name_item.set()
    elif msg.text == '📝 Редактировать описание':
        await bot.send_message(msg.from_user.id, f'▶️ Введите новое описание для товара', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_new_description_item.set()
    elif msg.text == '💵 Редактировать цену':
        await bot.send_message(msg.from_user.id, f'▶️ Введите новую цену для товара', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_new_price_item.set()
    elif msg.text == '❌ Удалить товар':
        sql.execute(f"DELETE FROM instances WHERE id_item = {selected_item}")
        sql.execute(f"DELETE FROM items WHERE id_item = {selected_item}")
        db.commit()

        log.info(f'{msg.from_user.id} deleted the product {selected_item}')

        sql.execute(f"SELECT name_item FROM items WHERE id_category = {selected_category}")
        list_item = sql.fetchall()

        list_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_item:
            list_item__kb.add(KeyboardButton(name[0]))

        list_item__button_1 = KeyboardButton('🤖Добавить новый')
        list_item__button_2 = KeyboardButton('◀ Назад')

        list_item__kb.add(list_item__button_1, list_item__button_2)

        if len(list_item) != 0:
            await bot.send_message(msg.from_user.id, f'🗑 Товар удален. Внизу список товаров в этой категории. Нажмите на любой, чтобы редактировать или удалить', reply_markup=list_item__kb)
        else:
            await bot.send_message(msg.from_user.id, f'🗑  Товар удален. У вас еще нету ни одного товара, создайте новый!', reply_markup=list_item__kb)

        await control_panel.wait_catogory_for_item.set()
    elif msg.text == '◀ Назад':
        log.info(f'{msg.from_user.id} returned to the list of products of the category')

        sql.execute(f"SELECT name_item FROM items WHERE id_category = {selected_category}")
        list_item = sql.fetchall()

        list_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_item:
            list_item__kb.add(KeyboardButton(name[0]))

        list_item__button_1 = KeyboardButton('🤖Добавить новый')
        list_item__button_2 = KeyboardButton('◀ Назад')

        list_item__kb.add(list_item__button_1, list_item__button_2)

        if len(list_item) != 0:
            await bot.send_message(msg.from_user.id, f'⬇️ Внизу список товаров в этой категории. Нажмите на любой, чтобы редактировать или удалить', reply_markup=list_item__kb)
        else:
            await bot.send_message(msg.from_user.id, f'🤷‍♂️ У вас еще нету ни одного товара, создайте новый!', reply_markup=list_item__kb)

        await control_panel.wait_catogory_for_item.set()
    elif msg.text == '‼️ Создать экземпляр':
        await bot.send_message(msg.from_user.id, f'▶️ Введите текст того, что получит клиент после покупки товара. Чтобы создать несколько экземпляров, разделяйте их переносом на новую строку', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_name_instance.set()
    elif msg.text == '👀 Список экземпляров':
        sql.execute(f"SELECT * FROM instances WHERE id_item = {selected_item}")
        list_instances = sql.fetchall()

        list_instances__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_instances:
            type_instance = ''
            if name[3] == 0:
                type_instance = '🔴 '
            elif name[3] == 1:
                type_instance = '🟢 '

            list_instances__kb.add(KeyboardButton(f'{type_instance}{name[2]}'))

        list_instances__kb.add(KeyboardButton('◀️ Назад'))

        if len(list_instances) == 0:
            await bot.send_message(msg.from_user.id, f'☹️ У этого товаров еще не создано экземпляров!', reply_markup=list_instances__kb)
        elif len(list_instances) != 0:
            await bot.send_message(msg.from_user.id, f'⬇️ Ниже представлен список экземпляров этого товара. Нажмите на любой, чтобы изменить текст или тип экземпляра', reply_markup=list_instances__kb)
        await control_panel.wait_instance.set()

# Ожидание экземпляра, который пользователь хочет изменить
@dp.message_handler(state=control_panel.wait_instance)
async def wait_instance(msg: types.Message):
    global selected_shop
    global selected_category
    global selected_item
    global selected_instance

    if msg.text == '◀️ Назад':
        sql.execute(f"SELECT name_item FROM items WHERE id_item = {selected_item}")
        name_item = sql.fetchone()[0]

        sql.execute(f"SELECT description_item FROM items WHERE id_item = {selected_item}")
        description_item = sql.fetchone()[0]

        sql.execute(f"SELECT price_item FROM items WHERE id_item = {selected_item}")
        price_item = sql.fetchone()[0]

        cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
        cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
        cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
        cp_item__button_4 = KeyboardButton('❌ Удалить товар')
        cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
        cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
        cp_item__button_7 = KeyboardButton('◀ Назад')

        cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

        await bot.send_message(msg.from_user.id, f'💢 Название товара: {name_item}\n\n⭕️ Описание товара: {description_item}\n\n💲 Цена товара: {price_item}\n\nВыберите действие над товаром', reply_markup=cp_item__kb)
        await control_panel.item_event.set()
    else:
        try:
            name_instance = (msg.text)[2:]
            sql.execute(f"SELECT id_instance FROM instances WHERE name_instance = '{name_instance}'")
            selected_instance = sql.fetchone()[0]

            edit_instance__kb = ReplyKeyboardMarkup(resize_keyboard=True)

            edit_instance__button_1 = KeyboardButton('✏️ Редактировать сообщение')
            edit_instance__button_2 = KeyboardButton('📝 Изменить тип')
            edit_instance__button_3 = KeyboardButton('❌ Удалить экземпляр')
            edit_instance__button_4 = KeyboardButton('◀ Назад')

            edit_instance__kb.add(edit_instance__button_1, edit_instance__button_2, edit_instance__button_3, edit_instance__button_4)

            await bot.send_message(msg.from_user.id, f'Экземпляр: {msg.text}\n\nВыберите действие над экземпляром', reply_markup=edit_instance__kb)

            await control_panel.wait_event_instance.set()
        except TypeError:
            pass

# Ожидаем действие над экземпляром
@dp.message_handler(state=control_panel.wait_event_instance)
async def wait_event_instance(msg: types.Message):
    global selected_item
    global selected_instance

    if msg.text == '✏️ Редактировать сообщение':
        await bot.send_message(msg.from_user.id, f'▶️ Введите текст нового сообщения для экземпляра', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_new_name_instance.set()
    elif msg.text == '📝 Изменить тип':
        type_of_instance__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        type_of_instance__button_1 = KeyboardButton('🟢 Многоразовый экземпляр')
        type_of_instance__button_2 = KeyboardButton('🔴 Одноразовый экземпляр')

        type_of_instance__kb.add(type_of_instance__button_1, type_of_instance__button_2)

        await bot.send_message(msg.from_user.id, f'▶️ Выберите новый тип для экземпляра', reply_markup=type_of_instance__kb)
        await control_panel.wait_new_type_instance.set()
    elif msg.text == '❌ Удалить экземпляр':
        sql.execute(f"DELETE FROM instances WHERE id_instance = {selected_instance}")
        db.commit()

        cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
        cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
        cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
        cp_item__button_4 = KeyboardButton('❌ Удалить товар')
        cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
        cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
        cp_item__button_7 = KeyboardButton('◀ Назад')

        cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

        await bot.send_message(msg.from_user.id, f'🗑 Экземпляр удален!', reply_markup=cp_item__kb)
        await control_panel.item_event.set()
    elif msg.text == '◀ Назад':
        sql.execute(f"SELECT * FROM instances WHERE id_item = {selected_item}")
        list_instances = sql.fetchall()

        list_instances__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_instances:
            type_instance = ''
            if name[3] == 0:
                type_instance = '🔴 '
            elif name[3] == 1:
                type_instance = '🟢 '

            list_instances__kb.add(KeyboardButton(f'{type_instance}{name[2]}'))

        list_instances__kb.add(KeyboardButton('◀️ Назад'))

        if len(list_instances) == 0:
            await bot.send_message(msg.from_user.id, f'☹️ У этого товаров еще не создано экземпляров!', reply_markup=list_instances__kb)
        elif len(list_instances) != 0:
            await bot.send_message(msg.from_user.id, f'⬇️ Ниже представлен список экземпляров этого товара. Нажмите на любой, чтобы изменить текст или тип экземпляра', reply_markup=list_instances__kb)
        await control_panel.wait_instance.set()

# Ожидаем новый тип экземпляра
@dp.message_handler(state=control_panel.wait_new_type_instance)
async def wait_new_type_instance(msg: types.Message):
    global selected_instance

    type_instance = -1

    if msg.text == '🟢 Многоразовый экземпляр':
        type_instance = 1
    elif msg.text == '🔴 Одноразовый экземпляр':
        type_instance = 0

    sql.execute(f'UPDATE instances SET type_of_instance = {type_instance} WHERE id_instance = {selected_instance}')
    db.commit()

    edit_instance__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    edit_instance__button_1 = KeyboardButton('✏️ Редактировать сообщение')
    edit_instance__button_2 = KeyboardButton('📝 Изменить тип')
    edit_instance__button_3 = KeyboardButton('❌ Удалить экземпляр')
    edit_instance__button_4 = KeyboardButton('◀ Назад')

    edit_instance__kb.add(edit_instance__button_1, edit_instance__button_2, edit_instance__button_3, edit_instance__button_4)

    await bot.send_message(msg.from_user.id, f'✅ Тип экземпляра изменен!', reply_markup=edit_instance__kb)
    await control_panel.wait_event_instance.set()

# Ожидаем новый текст экземпляра
@dp.message_handler(state=control_panel.wait_new_name_instance)
async def wait_new_name_instance(msg: types.Message):
    global selected_instance

    sql.execute(f"UPDATE instances SET name_instance = '{msg.text}' WHERE id_instance = {selected_instance}")
    db.commit()

    edit_instance__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    edit_instance__button_1 = KeyboardButton('✏️ Редактировать сообщение')
    edit_instance__button_2 = KeyboardButton('📝 Изменить тип')
    edit_instance__button_3 = KeyboardButton('❌ Удалить экземпляр')
    edit_instance__button_4 = KeyboardButton('◀ Назад')

    edit_instance__kb.add(edit_instance__button_1, edit_instance__button_2, edit_instance__button_3, edit_instance__button_4)

    await bot.send_message(msg.from_user.id, f'✅ Сообщение экземпляра изменено!', reply_markup=edit_instance__kb)
    await control_panel.wait_event_instance.set()

# Ожидаем текст экзампляра
@dp.message_handler(state=control_panel.wait_name_instance)
async def wait_name_instance(msg: types.Message, state: FSMContext):
    await state.update_data(name_instance=msg.text)

    type_of_instance__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    type_of_instance__button_1 = KeyboardButton('🟢 Многоразовый экземпляр')
    type_of_instance__button_2 = KeyboardButton('🔴 Одноразовый экземпляр')

    type_of_instance__kb.add(type_of_instance__button_1, type_of_instance__button_2)

    if '\n' in msg.text:
         await bot.send_message(msg.from_user.id, f'Выберите тип экземпляров:\n🟢 Многоразовый экземпляр - при покупке товара, экземпляр не удалится и его смогут купить еще раз\n🔴 Одноразовый экземпляр - при покупке товара, экзампляр удалится и больше никому не попадется', reply_markup=type_of_instance__kb)
    else:
        await bot.send_message(msg.from_user.id, f'Выберите тип экземпляра:\n🟢 Многоразовый экземпляр - при покупке товара, экземпляр не удалится и его смогут купить еще раз\n🔴 Одноразовый экземпляр - при покупке товара, экзампляр удалится и больше никому не попадется', reply_markup=type_of_instance__kb)
    await control_panel.wait_type_of_instance.set()

# Ожидаем тип экземпляра
@dp.message_handler(state=control_panel.wait_type_of_instance)
async def wait_type_of_instance(msg: types.Message, state: FSMContext):
    global selected_item

    type_instance = -1
    if msg.text == '🟢 Многоразовый экземпляр':
        type_instance = 1
    if msg.text == '🔴 Одноразовый экземпляр':
        type_instance = 0

    name_instance = await state.get_data()

    list_instance = name_instance['name_instance'].splitlines()

    for name in list_instance:
        try:
            sql.execute(f"SELECT * FROM instances WHERE ROWID IN (SELECT max(ROWID) FROM instances)")
            count_str = sql.fetchone()[1] + 1
        except TypeError:
            count_str = 0

        sql.execute("INSERT INTO instances VALUES (?, ?, ?, ?)", (selected_item, count_str, name, type_instance))
        db.commit()

    cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
    cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
    cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
    cp_item__button_4 = KeyboardButton('❌ Удалить товар')
    cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
    cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
    cp_item__button_7 = KeyboardButton('◀ Назад')

    cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

    await bot.send_message(msg.from_user.id, f'✅ Экземпляр успешно создан!', reply_markup=cp_item__kb)
    await control_panel.item_event.set()

# Ожидаем ввода нового названия товара
@dp.message_handler(state=control_panel.wait_new_name_item)
async def wait_new_name_item(msg: types.Message):
    global selected_item

    sql.execute(f"UPDATE items SET name_item = '{msg.text}' WHERE id_item = {selected_item}")
    db.commit()

    cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
    cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
    cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
    cp_item__button_4 = KeyboardButton('❌ Удалить товар')
    cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
    cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
    cp_item__button_7 = KeyboardButton('◀ Назад')

    cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

    await bot.send_message(msg.from_user.id, f'✅ Название товара изменено!', reply_markup=cp_item__kb)
    await control_panel.item_event.set()

# Ожидание ввода нового описания товара
@dp.message_handler(state=control_panel.wait_new_description_item)
async def wait_new_description_item(msg: types.Message):
    global selected_item

    sql.execute(f"UPDATE items SET description_item = '{msg.text}' WHERE id_item = {selected_item}")
    db.commit()

    cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
    cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
    cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
    cp_item__button_4 = KeyboardButton('❌ Удалить товар')
    cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
    cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
    cp_item__button_7 = KeyboardButton('◀ Назад')

    cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

    await bot.send_message(msg.from_user.id, f'✅ Описание товара изменено!', reply_markup=cp_item__kb)
    await control_panel.item_event.set()

# Ожидание ввода новой цены товара
@dp.message_handler(state=control_panel.wait_new_price_item)
async def wait_new_price_item(msg: types.Message):
    global selected_item

    sql.execute(f"UPDATE items SET price_item = {abs(int(msg.text))} WHERE id_item = {selected_item}")
    db.commit()

    cp_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cp_item__button_1 = KeyboardButton('✏️ Редактировать название')
    cp_item__button_2 = KeyboardButton('📝 Редактировать описание')
    cp_item__button_3 = KeyboardButton('💵 Редактировать цену')
    cp_item__button_4 = KeyboardButton('❌ Удалить товар')
    cp_item__button_5 = KeyboardButton('‼️ Создать экземпляр')
    cp_item__button_6 = KeyboardButton('👀 Список экземпляров')
    cp_item__button_7 = KeyboardButton('◀ Назад')

    cp_item__kb.add(cp_item__button_1, cp_item__button_2, cp_item__button_3, cp_item__button_4, cp_item__button_5, cp_item__button_6, cp_item__button_7)

    await bot.send_message(msg.from_user.id, f'✅ Цена товара изменена!', reply_markup=cp_item__kb)
    await control_panel.item_event.set()

# Ожидание ввода названия товара
@dp.message_handler(state=control_panel.wait_name_item)
async def wait_name_item(msg: types.Message, state: FSMContext):
    await state.update_data(name_item=msg.text)
    await bot.send_message(msg.from_user.id, f'▶️ Введите описание товара', reply_markup=ReplyKeyboardRemove())
    await control_panel.wait_description_item.set()

# Ожидание ввода описания товара
@dp.message_handler(state=control_panel.wait_description_item)
async def wait_description_item(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await bot.send_message(msg.from_user.id, f'▶️ Введите цену товара', reply_markup=ReplyKeyboardRemove())
    await control_panel.wait_price_item.set()

# Ожидание цены на товар
@dp.message_handler(state=control_panel.wait_price_item)
async def wait_price_item(msg: types.Message, state: FSMContext):
    global selected_category

    try:
        price = abs(int((msg.text).lstrip('0'))) # Удаляем нули в начале числа

        user_data = await state.get_data()

        try:
            sql.execute(f"SELECT * FROM items WHERE ROWID IN (SELECT max(ROWID) FROM items)")
            count_str = sql.fetchone()[1] + 1
        except TypeError:
            count_str = 0

        sql.execute(f"INSERT INTO items VALUES (?, ?, ?, ?, ?)", (int(selected_category), int(count_str), str(user_data['name_item']), str(user_data['description']), int(price)))
        db.commit()

        sql.execute(f"SELECT name_item FROM items WHERE id_category = {selected_category}")
        list_item = sql.fetchall()

        list_item__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_item:
            list_item__kb.add(KeyboardButton(name[0]))

        list_item__button_1 = KeyboardButton('🤖Добавить новый')
        list_item__button_2 = KeyboardButton('◀ Назад')

        list_item__kb.add(list_item__button_1, list_item__button_2)

        await bot.send_message(msg.from_user.id, f'✅ Товар добавлен!', reply_markup=list_item__kb)
        await control_panel.wait_catogory_for_item.set()
    except ValueError:
        await bot.send_message(msg.from_user.id, f'🟡 Кажется, это не число, а цена может быть только в виде числа. Попробуйте снова')

# Когда нажата кнопка Категории
@dp.message_handler(state=control_panel.post_category)
async def category(msg: types.Message):
    global selected_shop

    if msg.text == '◀ Назад':
        sql.execute(f"SELECT name_shop FROM shops WHERE id_shop = {selected_shop}")

        await bot.send_message(msg.from_user.id, f'⚙ Панель управления магазином «{sql.fetchone()[0]}». Выберите действие', reply_markup=buttons.control_panel__kb)
        await control_panel.wait_event.set()
    elif msg.text == '🤖Создать новую':
        await bot.send_message(msg.from_user.id, f'▶️ Введите название новой категории', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_name_category.set()
    else:
        global selected_category
        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")

        list_categories_shops = []
        for name in sql.fetchall():
            list_categories_shops.append(name[0])

        if msg.text in list_categories_shops:
            cp_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

            cp_categories__button_1 = KeyboardButton('✏️ Изменить название')
            cp_categories__button_2 = KeyboardButton('❌ Удалить категорию')
            cp_categories__button_3 = KeyboardButton('◀ Назад')

            cp_categories__kb.add(cp_categories__button_1, cp_categories__button_2, cp_categories__button_3)

            await bot.send_message(msg.from_user.id, f'👆 Выберите действие с категорией «{msg.text}»', reply_markup=cp_categories__kb)

            sql.execute(f"SELECT id_category FROM categories WHERE (id_shop = {selected_shop} and name_category = '{msg.text}')")
            selected_category = sql.fetchone()[0]

            await control_panel.categories_event.set()

# Ожидание введения названия новой категории
@dp.message_handler(state=control_panel.wait_name_category)
async def name_of_category(msg: types.Message):
    global selected_shop

    try:
        sql.execute(f"SELECT * FROM categories WHERE ROWID IN (SELECT max(ROWID) FROM categories)")
        count_str = sql.fetchone()[1] + 1
    except TypeError:
        count_str = 0

    sql.execute("INSERT INTO categories VALUES (?, ?, ?)", (int(selected_shop), int(count_str), str(msg.text)))
    db.commit()

    sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
    list_categories = sql.fetchall()

    list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for name in list_categories:
        list_categories__kb.add(KeyboardButton(name[0]))

    list_categories__button_1 = KeyboardButton('🤖Создать новую')
    list_categories__button_2 = KeyboardButton('◀ Назад')

    list_categories__kb.add(list_categories__button_1, list_categories__button_2)

    await bot.send_message(msg.from_user.id, f'✅ Категория с названием «{msg.text}» создана!', reply_markup=list_categories__kb)

    await control_panel.post_category.set()

# Выбираем действие с категорией
@dp.message_handler(state=control_panel.categories_event)
async def event_of_category(msg: types.Message):
    global selected_shop
    global selected_category

    if msg.text == '✏️ Изменить название':
        await bot.send_message(msg.from_user.id, f'▶️ Введите новое название для этой категории', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_new_name_category.set()
    elif msg.text == '❌ Удалить категорию':
        sql.execute(f"DELETE FROM categories WHERE id_category = {selected_category}")

        sql.execute(f"SELECT id_item FROM items WHERE id_category = {selected_category}")
        for id in sql.fetchall():
            sql.execute(f"DELETE FROM instances WHERE id_item = {id[0]}")
            sql.execute(f"DELETE FROM items WHERE id_item = {id[0]}")

        db.commit()

        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
        list_categories = sql.fetchall()

        list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_categories:
            list_categories__kb.add(KeyboardButton(name[0]))

        list_categories__button_1 = KeyboardButton('🤖Создать новую')
        list_categories__button_2 = KeyboardButton('◀ Назад')

        list_categories__kb.add(list_categories__button_1, list_categories__button_2)

        await bot.send_message(msg.from_user.id, f'🗑 Категория удалена!', reply_markup=list_categories__kb)

        await control_panel.post_category.set()
    elif msg.text == '◀ Назад':
        sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
        list_categories = sql.fetchall()

        list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for name in list_categories:
            list_categories__kb.add(KeyboardButton(name[0]))

        list_categories__button_1 = KeyboardButton('🤖Создать новую')
        list_categories__button_2 = KeyboardButton('◀ Назад')

        list_categories__kb.add(list_categories__button_1, list_categories__button_2)

        if len(list_categories) != 0:
            await bot.send_message(msg.from_user.id, f'🟡 Ниже список ваших категорий. Выберите любую, чтобы изменить ее название или удалить', reply_markup=list_categories__kb)
        else:
            await bot.send_message(msg.from_user.id, f'У вас еще нет категории, создайте новую', reply_markup=list_categories__kb)
        await control_panel.post_category.set()

# Ждем новое название для категории
@dp.message_handler(state=control_panel.wait_new_name_category)
async def new_name_category(msg: types.Message):
    global selected_shop
    global selected_category

    sql.execute(f"UPDATE categories SET name_category = '{msg.text}' WHERE id_category = '{selected_category}'")
    db.commit()

    sql.execute(f"SELECT name_category FROM categories WHERE id_shop = '{selected_shop}'")
    list_categories = sql.fetchall()

    list_categories__kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for name in list_categories:
        list_categories__kb.add(KeyboardButton(name[0]))

    list_categories__button_1 = KeyboardButton('🤖Создать новую')
    list_categories__button_2 = KeyboardButton('◀ Назад')

    list_categories__kb.add(list_categories__button_1, list_categories__button_2)

    await bot.send_message(msg.from_user.id, f'✅ Название категории изменено!', reply_markup=list_categories__kb)

    await control_panel.post_category.set()

# Если нажата кнопка Личный кабинет
@dp.message_handler(state=menu.account)
async def command_account(msg: types.Message):
    if msg.text == '◀ Назад':
        await bot.send_message(msg.from_user.id, f'📌 Вы в главном меню!', reply_markup=buttons.mainmenu__kb)
        await menu.mainmenu.set()
    elif msg.text == '💰 Вывести':
        sql.execute(f"SELECT balance FROM users WHERE id_user = {msg.from_user.id}")
        balance = sql.fetchone()[0]
        if balance == 0:
            await bot.send_message(msg.from_user.id, f'🙅 На вашем балансе недостаточно денег для вывода!')
        elif balance != 0:
            sql.execute(f"SELECT status FROM withdrawal WHERE id_user = {msg.from_user.id}")
            status = sql.fetchall()

            if status == [] or status[-1][0] == 1:
                payments__kb = ReplyKeyboardMarkup(resize_keyboard=True)

                payments__button_1 = KeyboardButton('🥝 QIWI Кошелек')
                payments__button_2 = KeyboardButton('💳 Карта')
                payments__button_3 = KeyboardButton('👁‍🗨 ЮMoney')

                payments__kb.add(payments__button_1, payments__button_2, payments__button_3)

                await bot.send_message(msg.from_user.id, f'⁉️ Куда вы хотите принять средства?', reply_markup=payments__kb)
                await control_panel.wait_payments.set()
            elif status[-1][0] == 0:
                await bot.send_message(msg.from_user.id, f'🤠 У вас уже есть открытая заявка на вывод. Дождитесь предыдущего вывода, прежде чем создавать новую заявку')

# Когда ждем системы, куда пользователь хочет принять средства (киви, карта, юмани)
@dp.message_handler(state=control_panel.wait_payments)
async def wait_payments(msg: types.Message):
    if msg.text == '🥝 QIWI Кошелек':
        await bot.send_message(msg.from_user.id, f'📄 Введите реквизиты вашего QIWI Кошелька', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_qiwi_requisites.set()
    elif msg.text == '💳 Карта':
        await bot.send_message(msg.from_user.id, f'📄 Введите реквизиты вашей карты', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_card_requisites.set()
    elif msg.text == '👁‍🗨 ЮMoney':
        await bot.send_message(msg.from_user.id, f'📄 Введите реквизиты вашего ЮMoney', reply_markup=ReplyKeyboardRemove())
        await control_panel.wait_yoomoney_requisites.set()

# Тут мы принимаем реквизиты qiwi и отправляем сообщение первому админу
@dp.message_handler(state=control_panel.wait_qiwi_requisites)
async def wait_qiwi_requisites(msg: types.Message):
    sql.execute(f"SELECT id_user FROM users WHERE admin = 1")
    admin = sql.fetchone()[0]

    sql.execute(f"SELECT balance FROM users WHERE id_user = {msg.from_user.id}")
    balance = sql.fetchone()[0]

    try:
        sql.execute(f"SELECT * FROM withdrawal WHERE ROWID IN (SELECT max(ROWID) FROM withdrawal)")
        count_str = sql.fetchone()[1] + 1
    except TypeError:
        count_str = 0

    sql.execute(f"INSERT INTO withdrawal VALUES (?, ?, ?, ?, ?, ?)", (int(msg.from_user.id), int(count_str), 'qiwi', int(balance), msg.text, 0))
    db.commit()

    back__kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('◀ Назад'))
    await bot.send_message(msg.from_user.id, f'🔮 Ваша заявка на вывод создана! Ожидайте, когда вывод будет произведен, со счета в боте спишутся деньги', reply_markup=back__kb)

    paid__cb = CallbackData('paid', 'id_p')
    paid__button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Оплатил!', callback_data=paid__cb.new(id_p=count_str))]])
    await bot.send_message(admin, f'Новая заявка на вывод!\n\n👤 Пользователь: {msg.from_user.first_name} ({msg.from_user.id})\n🥝 Система: QIWI Кошелек\n💲 Сумма: {balance} руб.\n📃 Реквизиты: ```{msg.text}```', reply_markup=paid__button, parse_mode='Markdown')

    await menu.account.set()

# Тут мы принимаем реквизиты card и отправляем сообщение первому админу
@dp.message_handler(state=control_panel.wait_card_requisites)
async def wait_qiwi_requisites(msg: types.Message):
    sql.execute(f"SELECT id_user FROM users WHERE admin = 1")
    admin = sql.fetchone()[0]

    sql.execute(f"SELECT balance FROM users WHERE id_user = {msg.from_user.id}")
    balance = sql.fetchone()[0]

    try:
        sql.execute(f"SELECT * FROM withdrawal WHERE ROWID IN (SELECT max(ROWID) FROM withdrawal)")
        count_str = sql.fetchone()[1] + 1
    except TypeError:
        count_str = 0

    sql.execute(f"INSERT INTO withdrawal VALUES (?, ?, ?, ?, ?, ?)", (int(msg.from_user.id), int(count_str), 'card', int(balance), msg.text, 0))
    db.commit()

    back__kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('◀ Назад'))
    await bot.send_message(msg.from_user.id, f'🔮 Ваша заявка на вывод создана! Ожидайте, когда вывод будет произведен, со счета в боте спишутся деньги', reply_markup=back__kb)

    paid__cb = CallbackData('paid', 'id_p')
    paid__button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Оплатил!', callback_data=paid__cb.new(id_p=count_str))]])
    await bot.send_message(admin, f'Новая заявка на вывод!\n\n👤 Пользователь: {msg.from_user.first_name} ({msg.from_user.id})\n💳 Система: Карта\n💲 Сумма: {balance} руб.\n📃 Реквизиты: ```{msg.text}```', reply_markup=paid__button, parse_mode='Markdown')

    await menu.account.set()

# Тут мы принимаем реквизиты yoomoney и отправляем сообщение первому админу
@dp.message_handler(state=control_panel.wait_yoomoney_requisites)
async def wait_qiwi_requisites(msg: types.Message):
    sql.execute(f"SELECT id_user FROM users WHERE admin = 1")
    admin = sql.fetchone()[0]

    sql.execute(f"SELECT balance FROM users WHERE id_user = {msg.from_user.id}")
    balance = sql.fetchone()[0]

    try:
        sql.execute(f"SELECT * FROM withdrawal WHERE ROWID IN (SELECT max(ROWID) FROM withdrawal)")
        count_str = sql.fetchone()[1] + 1
    except TypeError:
        count_str = 0

    sql.execute(f"INSERT INTO withdrawal VALUES (?, ?, ?, ?, ?, ?)", (int(msg.from_user.id), int(count_str), 'yoomoney', int(balance), msg.text, 0))
    db.commit()

    back__kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('◀ Назад'))
    await bot.send_message(msg.from_user.id, f'🔮 Ваша заявка на вывод создана! Ожидайте, когда вывод будет произведен, со счета в боте спишутся деньги', reply_markup=back__kb)

    paid__cb = CallbackData('paid', 'id_p')
    paid__button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Оплатил!', callback_data=paid__cb.new(id_p=count_str))]])
    await bot.send_message(admin, f'Новая заявка на вывод!\n\n👤 Пользователь: {msg.from_user.first_name} ({msg.from_user.id})\n👁‍🗨 Система: ЮMoney\n💲 Сумма: {balance} руб.\n📃 Реквизиты: ```{msg.text}```', reply_markup=paid__button, parse_mode='Markdown')

    await menu.account.set()

@dp.callback_query_handler(lambda callback_query: True, state='*')
async def inline_button(call: types.CallbackQuery):
    await call.answer(cache_time=2)
    r = re.findall(r'([a-z_]*):([0-9]*)', call.data)

    sql.execute(f"SELECT id_user FROM withdrawal WHERE id_paid = {r[0][1]}")
    id_user = sql.fetchone()[0]

    sql.execute(f"SELECT amount FROM withdrawal WHERE id_paid = {r[0][1]}")
    amount = sql.fetchone()[0]

    sql.execute(f"SELECT balance FROM users WHERE id_user = {id_user}")
    balance = sql.fetchone()[0] - amount

    sql.execute(f"UPDATE users SET balance = {balance} WHERE id_user = {id_user}")
    db.commit()

    sql.execute(f"UPDATE withdrawal SET status = 1 WHERE id_paid = {r[0][1]}")
    db.commit()

    await call.message.edit_text(f'✅ Оплачено!')

async def on_startup(_):
    sql.execute(f"SELECT id_user FROM users")
    all_users = sql.fetchall()

    for user in all_users:
        sql.execute(f"SELECT * FROM shops WHERE id_user = {user[0]}")
        count_shops = sql.fetchall()

        if len(count_shops) == 0:
            await bot.send_message(user[0], f'🔄 Бот был обновлен! Введите команду /start для перезагрузки бота', reply_markup=ReplyKeyboardRemove())
        elif len(count_shops) == 1:
            await bot.send_message(user[0], f'🔄 Бот был обновлен! Введите команду /start для перезагрузки бота.\n\nТакже, ваш магазин «{count_shops[0][2]}» был приостановлен. Чтобы его запустить, воспользуйтесь панелью управления магазином', reply_markup=ReplyKeyboardRemove())
        elif len(count_shops) > 1:
            await bot.send_message(user[0], f'🔄 Бот был обновлен! Введите команду /start для перезагрузки бота.\n\nТакже, ваши магазины были приостановлены. Чтобы их запустить, воспользуйтесь панелью управления магазином', reply_markup=ReplyKeyboardRemove())

        await asyncio.sleep(1)

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
