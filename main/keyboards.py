import json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from table import get_shop_adresses
from shops import get_shop_name, get_shop_id


def get_start_keyboard():
	btn = KeyboardButton('Начать смену')
	keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
	keyboard.add(btn)
	return keyboard


def get_user_keyboard():
	btn = KeyboardButton('Расход')
	keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
	keyboard.add(btn)
	return keyboard


def get_cancel_keyboard():
	btn = InlineKeyboardButton('Отменить', callback_data='cancel')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(btn)
	return keyboard


def get_admin_keyboard():
	btn_1 = InlineKeyboardButton('Добавить супервайзера', callback_data='add_staff')
	btn_2 = InlineKeyboardButton('Проверить алгоритм пользователя', callback_data='check_user')
	btn_3 = InlineKeyboardButton('Проверить алгоритм супервайзера', callback_data='check_staff')
	keyboard = InlineKeyboardMarkup(row_width=1).add(btn_1, btn_2, btn_3)
	return keyboard


def get_time_keyboard():
	times_keyboard = InlineKeyboardMarkup(row_width=1)
	times_keyboard.add(
		InlineKeyboardButton('Дневная 24/7', callback_data='day'),
		InlineKeyboardButton('Дневная', callback_data='day_only'),
		InlineKeyboardButton('Ночная', callback_data='night')
	)
	return times_keyboard


def get_shops_keyboard(time):
	with open('shops.json', 'r', encoding='utf-8') as shops:
		data = json.load(shops)
	shops_keyboard = InlineKeyboardMarkup(row_width=3)
	for shop_id, shop_addresses in data['shop_addresses'][time].items():
		shops_keyboard.add((InlineKeyboardButton(shop_id[5:], callback_data=shop_id)))

	return shops_keyboard


def get_work_start_keyboard():
	yes_btn = InlineKeyboardButton('Систему 1С открыла', callback_data='work_start')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_shop_status_keyboard():
	yes_btn = InlineKeyboardButton('Да', callback_data='status_shop_yes')
	no_btn = InlineKeyboardButton('Нет', callback_data='status_shop_no')
	keyboard = InlineKeyboardMarkup(row_width=2)
	keyboard.add(yes_btn, no_btn)
	return keyboard


def get_layout_keyboard():
	yes_btn = InlineKeyboardButton('Товар разложен', callback_data='layout_yes')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_cleaning_keyboard():
	yes_btn = InlineKeyboardButton('Всё чисто', callback_data='cleaning_yes')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_send_photo_keyboard():
	yes_btn = InlineKeyboardButton('Отправила', callback_data='send_photo_yes')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_send_cash_keyboard():
	btn = InlineKeyboardButton('Средства получены', callback_data='send_cash_yes')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(btn)
	return keyboard


def get_continue_keyboard():
	yes_btn = InlineKeyboardButton('Продолжить', callback_data='continue')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_revision_keyboard():
	yes_btn = InlineKeyboardButton('Ревизия проведена', callback_data='revision_yes')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_expiration_date_keyboard():
	yes_btn = InlineKeyboardButton('Срок годности проверен', callback_data='expiration_date_yes')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_work_done_keyboard():
	no_btn = InlineKeyboardButton('Закрыла смену в 1С', callback_data='is_work_no')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(no_btn)
	return keyboard


def get_done_keyboard():
	yes_btn = InlineKeyboardButton('КОНЕЦ', callback_data='exit')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(yes_btn)
	return keyboard


def get_purchases_keyboard():
	btn = InlineKeyboardButton('Начать', callback_data='purchases_start')
	keyboard = InlineKeyboardMarkup()
	keyboard.add(btn)
	return keyboard
