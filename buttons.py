from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

mainmenu__button_1 = KeyboardButton('🛒 Мои магазины')
mainmenu__button_2 = KeyboardButton('🔓 Личный кабинет')

mainmenu__kb = ReplyKeyboardMarkup(resize_keyboard=True).add(mainmenu__button_1, mainmenu__button_2)

account__button_1 = KeyboardButton('💰 Вывести')
account__button_2 = KeyboardButton('◀ Назад')

account__kb = ReplyKeyboardMarkup(resize_keyboard=True).add(account__button_1, account__button_2)

control_panel__button_1 = KeyboardButton('📦 Категории')
control_panel__button_2 = KeyboardButton('🎈 Товары')
control_panel__button_3 = KeyboardButton('⚙ Тех. поддержка')
control_panel__button_4 = KeyboardButton('👥 Реферальная система')
control_panel__button_5 = KeyboardButton('📃 Актуальный купон')
control_panel__button_6 = KeyboardButton('❌ Удалить магазин')
control_panel__button_7 = KeyboardButton('✏️ Изменить название')
control_panel__button_8 = KeyboardButton('⏯ Запустить/остановить')
control_panel__button_9 = KeyboardButton('✉️ Рассылка')
control_panel__button_10 = KeyboardButton('◀ Назад')

control_panel__kb = ReplyKeyboardMarkup(resize_keyboard=True).add(control_panel__button_1, control_panel__button_2, control_panel__button_3, control_panel__button_4, control_panel__button_5, control_panel__button_6, control_panel__button_7, control_panel__button_8, control_panel__button_9, control_panel__button_10)
