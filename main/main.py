import logging
import json
import re
from asyncio import sleep, create_task, get_event_loop
from datetime import datetime
from pytz import timezone
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from auth import is_user, is_staff, is_admin
from users import *
from shops import update_info_shops
from table import *
from keyboards import *

with open('config.json', 'r', encoding='utf-8') as config:
	data = json.load(config)
	API_TOKEN = data['TOKEN']
	SERVICE_CHAT_ID = data['SERVICE_CHAT_ID']

# logging.basicConfig(filename="bot_log.log", filemode="a", level=logging.ERROR)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


def time_now():
	return timezone('Europe/Saratov').localize(datetime.now())


class UserState(StatesGroup):
	time = State()
	shop = State()
	fullname = State()
	shop_status = State()
	is_work = State()
	loss_count = State()
	loss_cause = State()
	revenue = State()
	terminal = State()
	collection = State()
	water_counter = State()
	light_counter = State()
	connected_kegs = State()
	full_kegs = State()
	# Закупки
	packages_large = State()
	packing_bags = State()
	glasses = State()
	containers_small = State()
	containers_large = State()
	cling_film = State()
	weight_tape = State()
	receipt_tape = State()
	soft_overhead = State()


class StaffState(StatesGroup):
	loss_count = State()
	loss_cause = State()
	income_count = State()
	income_cause = State()


class AdminState(StatesGroup):
	user_id = State()
	fullname = State()


cash_re = re.compile(r"\d+")


async def set_menu(role: str, chat_id: int):
	scope = types.BotCommandScopeChat(chat_id)
	if role == 'admin':
		await bot.set_my_commands(
			[
				types.BotCommand('/start', 'Начать'),
				types.BotCommand('/clear_staff', 'Очистить список супервайзеров'),
				types.BotCommand('/help', 'Помощь'),
			],
			scope=scope
		)
	elif role == 'staff':
		await bot.set_my_commands(
			[
				types.BotCommand('/start', 'Начать смену'),
				types.BotCommand('/loss', 'Расход'),
				types.BotCommand('/income', 'Приход'),
				types.BotCommand('/help', 'Помощь'),

			],
			scope=scope
		)
	elif role == 'user':
		await bot.set_my_commands(
			[
				types.BotCommand('/start', 'Начать смену'),
				types.BotCommand('/loss', 'Расход'),
				types.BotCommand('/collection', 'Инкассация'),
				types.BotCommand('/help', 'Помощь'),
			],
			scope=scope
		)


def only_digits(text: str):
	return ''.join(digit for digit in text if digit.isdigit())


@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
	if state:
		await state.finish()
	if is_admin(message.from_user.id):
		await set_menu('admin', message.from_user.id)
		await message.reply(
			'Здравствуйте! Вы зашли под административной учётной записью.',
			reply_markup=get_admin_keyboard()
		)
	elif is_staff(message.from_user.id):
		print('staff')
		await set_menu('staff', message.from_user.id)
		await message.reply(
			text='Здравствуйте! Вы зашли под учетной записью супервайзера',
			reply_markup=get_start_keyboard()
		)
	elif is_user(message.from_user.id):
		print('user')
		await set_menu('user', message.from_user.id)
		await message.reply(
			'Здравствуйте! Вы зашли под пользовательской учетной записью',
			reply_markup=get_start_keyboard()
		)
	else:
		await message.reply("Тебя нет в моём списке. Обратись к руководству.")


@dp.callback_query_handler(lambda c: 'check_user' in c.data, state='*')
async def check_user(callback_query: types.CallbackQuery):
	if is_admin(callback_query.message.chat.id):
		await callback_query.message.answer(text='Пару секунд, проверяю настройки...')
		set_user_temple(callback_query.message.chat.id)
		if not list_exist():
			await callback_query.message.answer(
				'В БД нет листа с текущей датой. Начинаю его создавать, ожидайте около 15 секунд')
			create_main_list()
		update_info_shops()
		await callback_query.message.answer('Выберете свою смену:', reply_markup=get_time_keyboard())
		await UserState.fullname.set()


@dp.message_handler(text=['Начать смену'])
async def start_work(message: types.Message):
	if is_staff(message.from_user.id):
		keyboard = InlineKeyboardMarkup()
		keyboard.add(
			InlineKeyboardButton('Подтвердить', callback_data='accept_check'),
			InlineKeyboardButton('Отменить', callback_data='cancel')
		)
		await message.answer(
			'Проведите проверку всех отчётов и нажмите кнопку "Подтвердить"',
			reply_markup=keyboard
		)
	elif is_user(message.from_user.id):
		await message.answer(text='Пару секунд, проверяю настройки...')
		set_user_temple(message.from_user.id)
		if not list_exist():
			await message.answer('В БД нет листа с текущей датой. Начинаю его создавать, ожидайте около 15 секунд')
			create_main_list()
		update_info_shops()
		await message.answer("Выберете свою смену:", reply_markup=get_time_keyboard())
		await UserState.fullname.set()


@dp.callback_query_handler(lambda c: 'accept_check' in c.data)
async def main_menu_staff(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		update_finance_staff_list('Проверка фото-отчётов')
		await callback_query.message.answer('Принято! Переход в главное меню')


@dp.callback_query_handler(lambda c: 'cancel' in c.data, state='*')
async def back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
	if state:
		await state.finish()
	if is_admin(callback_query.message.chat.id):
		await callback_query.message.answer('Возврат в главное меню', reply_markup=get_admin_keyboard())
	elif is_staff(callback_query.message.chat.id):
		await callback_query.message.answer('Возврат в главное меню')
	elif is_user(callback_query.message.chat.id):
		await callback_query.message.answer('Возврат в главное меню')


@dp.message_handler(commands='collection')
async def collection_get_count(message: types.Message):
	if is_user(message.chat.id):
		await message.answer(
			'Укажите сумму, которую забрали из кассы цифрами в следующем сообщении или нажмите "Отменить"',
			reply_markup=get_cancel_keyboard()
		)
		await UserState.collection.set()


@dp.message_handler(state=UserState.collection)
async def collection_get_shop(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(collection_count=message.text)
		data = await state.get_data()
		update_finance_user_list(message.from_user.id, '-', {'collection': data['collection_count']})
		await message.answer('Принято!', reply_markup=get_user_keyboard())
		await state.finish()


@dp.message_handler(commands='loss')
async def get_loss(message: types.Message):
	if is_staff(message.chat.id):
		await message.answer(
			'Отправьте сумму расхода цифрами следующим сообщением или нажмите кнопку "Отменить"',
			reply_markup=get_cancel_keyboard(),
		)
		await StaffState.loss_count.set()
	elif is_user(message.chat.id):
		await message.answer(
			'Отправьте сумму расхода цифрами следующим сообщением или нажмите кнопку "Отменить"',
			reply_markup=get_cancel_keyboard(),
		)
		await UserState.loss_count.set()


@dp.message_handler(state=StaffState.loss_count)
@dp.message_handler(state=UserState.loss_count)
async def post_loss(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(loss_count=message.text)
		data = await state.get_data()
		await message.answer(
			'Отправьте адрес магазина следующим сообщением или нажмите "Отменить"',
			reply_markup=get_cancel_keyboard()
		)
		await StaffState.loss_cause.set()
	elif is_user(message.chat.id):
		await state.update_data(loss_count=message.text)
		data = await state.get_data()
		await message.answer(
			'Отправьте причину расхода следующим сообщением или нажмите "Отменить"',
			reply_markup=get_cancel_keyboard()
		)
		await UserState.loss_cause.set()


@dp.message_handler(state=StaffState.loss_cause)
@dp.message_handler(state=UserState.loss_cause)
async def post_loss(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(loss_cause=message.text)
		data = await state.get_data()
		update_finance_staff_list(data['loss_cause'], {'loss': data['loss_count']})
		await message.answer('Принято!')
	elif is_user(message.chat.id):
		await state.update_data(loss_cause=message.text)
		data = await state.get_data()
		update_finance_user_list(message.from_user.id, data['loss_cause'], {'loss': data['loss_count']})
		await message.answer('Принято!')
	await state.finish()


@dp.callback_query_handler(lambda c: 'check_staff' in c.data)
async def staff_start(callback_query: types.CallbackQuery):
	if is_admin(callback_query.message.chat.id) or is_staff(callback_query.message.chat.id):
		await callback_query.message.answer(
			text='Здравствуйте! Вы зашли под учетной записью супервайзера',
			reply_markup=get_start_keyboard()
		)


@dp.message_handler(commands='income')
async def get_income_count(message: types.Message):
	if is_staff(message.chat.id):
		await message.answer('Введите сумму прихода цифрами в следующем сообщении')
		await StaffState.income_count.set()


@dp.message_handler(state=StaffState.income_count)
async def get_income_cause(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(income_count=message.text)
		await message.answer('Введите адрес магазина в следующем сообщении')
		await StaffState.income_cause.set()


@dp.message_handler(state=StaffState.income_cause)
async def send_income(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(income_cause=message.text)
		data = await state.get_data()
		await state.finish()
		update_finance_staff_list(data['income_cause'], {'income': data['income_count']})
		await message.answer('Принято!')


@dp.callback_query_handler(lambda c: 'day' in c.data or 'night' in c.data, state='*')
async def send_shops(callback_query: types.CallbackQuery, state: FSMContext):
	if is_user(callback_query.message.chat.id):
		await state.update_data(time=callback_query.data)
		data = await state.get_data()
		change_user_info(callback_query.message.chat.id, {"time": data['time']})
		await state.finish()
		await callback_query.message.answer('Принято!')
		await callback_query.message.answer(
			'Выберите номер магазина:',
			reply_markup=get_shops_keyboard(data['time'])
		)


@dp.callback_query_handler(lambda c: 'add_staff' in c.data)
async def await_staff_id(callback_query: types.CallbackQuery):
	await callback_query.message.answer('Напишите id пользователя, которого нужно добавить в "Супервайзеры"')
	await AdminState.user_id.set()


@dp.message_handler(state=AdminState.user_id)
async def await_fullname_staff(message: types.Message, state: FSMContext):
	await state.update_data(user_id=message.text)
	data = await state.get_data()
	add_staff(data['user_id'])
	await message.answer('Введите полные Ф.И.О. супервайзера')
	await AdminState.fullname.set()


@dp.message_handler(state=AdminState.fullname)
async def add_staff_func(message: types.Message, state: FSMContext):
	try:
		await state.update_data(fullname=message.text)
		data = await state.get_data()
		add_staff(data['user_id'], data['fullname'])
		await state.finish()
		await message.reply('Пользователь добавлен в список администраторов')
	except KeyError:
		await message.answer('Что-то пошло не так и я попытался исправить это. Попробуй ещё раз')
		await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('shop_'), state='*')
async def send_fullname(callback_query: types.CallbackQuery, state: FSMContext):
	if is_user(callback_query.message.chat.id):
		await state.update_data(shop=callback_query.data)
		data = await state.get_data()
		change_user_info(
			callback_query.message.chat.id,
			{
				"shop": data['shop'],
				"row": data['shop'][5:],
			}
		)
		await callback_query.message.answer('Принято!')
		await callback_query.message.answer('Напишите своё ФИО:')
		await UserState.fullname.set()


@dp.message_handler(state=UserState.fullname)
async def send_fullname(message: types.Message, state: FSMContext):
	if is_user(message.from_user.id):
		await state.update_data(fullname=message.text)
		data = await state.get_data()
		fullname = data['fullname']
		if check_fields(message.chat.id) is not None:
			await message.answer(
				f'В этом магазине уже работает {check_fields(message.chat.id)}\n'
				'Выберите другой:',
				reply_markup=get_time_keyboard()
			)
		else:
			change_user_info(message.from_user.id, data)
			update_main_table_fields(message.from_user.id)
			await state.finish()
			await message.answer('Принято!')
			await message.answer(
				f'Начинаем смену, {fullname}!\nОткрой смену в 1С и нажми на кнопку ниже',
				reply_markup=get_work_start_keyboard()
			)


@dp.callback_query_handler(lambda c: c.data.startswith('work_start'))
async def send_work_start(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		data = {'work_start': f"{time_now().strftime('%H:%M')}"}
		change_user_info(callback_query.message.chat.id, data)
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			f'Визуально в магазине/на складе все целое и все в порядке?',
			reply_markup=get_shop_status_keyboard()
		)


@dp.callback_query_handler(lambda c: 'status_shop_yes' in c.data)
async def send_cash_yes(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"shop_status": "Без особенностей"})
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			f'Прими денежные средства и нажми на кнопку "Средства получены".',
			reply_markup=get_send_cash_keyboard()
		)


@dp.callback_query_handler(lambda c: c.data.startswith('status_shop_no'))
async def send_status_shop_comment(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		await callback_query.message.answer(
			f'Прокомментируй недочет состояния магазина в ответном сообщении и постарайся его устранить. Позже во всём'
			' разберемся'
		)
		await UserState.shop_status.set()


@dp.message_handler(state=UserState.shop_status)
async def send_cash_no(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		shop_status = message.text
		await state.finish()
		change_user_info(message.chat.id, {"shop_status": shop_status})
		update_main_table_fields(message.chat.id)
		await message.answer('Принято!', reply_markup=get_user_keyboard())
		await message.answer(
			f'Прими денежные средства и нажми на кнопку "Средства получены".',
			reply_markup=get_send_cash_keyboard()
		)


@dp.callback_query_handler(lambda c: 'send_cash_yes' in c.data)
async def send_layout(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {'cash': "'+"})
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer(f'Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Разложи товар, по окончанию нажми на кнопку "Товар разложен"',
			reply_markup=get_layout_keyboard()
		)


@dp.callback_query_handler(lambda c: c.data.startswith('layout_yes'))
async def send_cleaning(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"layout": "'+"})
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Уберись в помещении (протирка кранов, протирка всех поверхностей, проверить чистоту окон и стёкол витрин)'
			'и нажми на кнопку "Все чисто"',
			reply_markup=get_cleaning_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('cleaning_yes'))
async def send_photo(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"cleaning": "'+"})
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Отправь Фото отчет в группу с Админом до 11.00 (Электроэнергия, Раскладка, Фасад магазина, лист смены кег)'
			'и нажми кнопку отправила,',
			reply_markup=get_send_photo_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('send_photo_yes'))
async def send_continue(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"send_photo": "'+"})
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'После проверки ты получишь до 10 баллов, Продолжай! (нажать на кнопку "Продолжить")',
			reply_markup=get_continue_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('continue'))
async def send_expiration_date(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Проверь сроки годности товаров и нажать на кнопку "Срок годности проверен"',
			reply_markup=get_expiration_date_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('expiration_date_yes'))
async def send_work_done(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"expiration_date": "'+"})
		update_main_table_fields(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Закрой смену в 1С и нажми на кнопку "Закрыла смену 1С"',
			reply_markup=get_work_done_keyboard(),
		)


@dp.callback_query_handler(lambda c: 'is_work_no' in c.data)
async def send_revenue_or_exit(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"work_done": f"{time_now().strftime('%H:%M')}"})
		update_main_table_fields(callback_query.message.chat.id)
		if get_user_info(callback_query.message.chat.id)['time'] == 'day_only':
			set_user_temple(callback_query.message.from_user.id)
			await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
			await callback_query.message.answer(
				'На этом всё. Хорошего отдыха!\nКак выйдешь на смену - просто нажми "Начать смену"',
				reply_markup=get_start_keyboard(),
			)
		else:
			await callback_query.message.answer('Напиши полученную выручку из кассы цифрами в следующем сообщении')
			await UserState.revenue.set()


@dp.message_handler(state=UserState.revenue)
async def send_terminal(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(revenue=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'revenue': only_digits(data['revenue'])})
		update_main_table_fields(message.chat.id)
		await message.answer('Принято!\nТеперь напиши выручку с терминала цифрами в следующем сообщении')
		await UserState.terminal.set()


@dp.message_handler(state=UserState.terminal)
async def send_collection_or_exit(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(terminal=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'terminal': only_digits(data['terminal'])})
		update_main_table_fields(message.chat.id)
		if get_user_info(message.chat.id)['time'] == 'day':
			await message.answer(
				'На этом всё. Хорошего отдыха!\nКак выйдешь на смену - просто нажми "Начать смену"',
				reply_markup=get_start_keyboard(),
			)
		elif get_user_info(message.chat.id)['time'] == 'night':
			await message.answer('Принято! Введите сумму для инкассации цифрами в следующем сообщении')
			await UserState.collection.set()


@dp.message_handler(state=UserState.collection)
async def send_water_counter(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(collection=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'collection': only_digits(data['collection'])})
		update_main_table_fields(message.chat.id)
		await message.answer('Принято! Введите показания счётчика воды')
		await UserState.water_counter.set()


@dp.message_handler(state=UserState.water_counter)
async def send_light_counter(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(water_counter=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'water_counter': only_digits(data['water_counter'])})
		await message.answer('Принято! Введите показания счётчика света')
		await UserState.light_counter.set()


@dp.message_handler(state=UserState.light_counter)
async def send_connected_kegs(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(light_counter=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'light_counter': only_digits(data['light_counter'])})
		update_meters_table_fields(message.chat.id)
		await message.answer('Принято! Введите количество подключенных кег')
		await UserState.connected_kegs.set()


@dp.message_handler(state=UserState.connected_kegs)
async def send_full_kegs(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(connected_kegs=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'connected_kegs': only_digits(data['connected_kegs'])})
		update_main_table_fields(message.chat.id)
		await message.answer('Принято! Введите количество полных кег')
		await UserState.full_kegs.set()


@dp.message_handler(state=UserState.full_kegs)
async def send_cleaning(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(full_kegs=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'full_kegs': only_digits(data['full_kegs'])})
		update_main_table_fields(message.chat.id)
		set_user_temple(message.from_user.id)
		await message.answer('Принято!', reply_markup=get_user_keyboard())
		await message.answer(
			'На этом всё. Хорошего отдыха!\nКак выйдешь на смену - просто нажми "Начать смену"',
			reply_markup=get_start_keyboard(),
		)


async def on_start_up_tasks(dp: Dispatcher):
	create_task(init_purchases())
	await bot.send_message(SERVICE_CHAT_ID, text='🔵Запускаю бота.\nПроизвожу настройки...')
	message = await bot.send_message(SERVICE_CHAT_ID, text='Создаю таблицы...')
	response_main = create_main_list()
	await message.edit_text(f'🔵 Создаю таблицы...\n      📋 Главная: {response_main}')
	response_meters = create_meters_list()
	await message.edit_text(
		f'🔵 Создаю таблицы...\n      📋 Главная: {response_main}\n      📋 Счётчики: {response_meters}')
	response_consumables = create_consumables_list()
	await message.edit_text(
		f'🔵 Создаю таблицы...\n      📋 Главная: {response_main}\n      📋 Счётчики: {response_meters}\n      📋 Закупки: {response_consumables}')
	response_finances_users = create_finance_user_list()
	await message.edit_text(
		f'🔵 Создаю таблицы...\n'
		f'      📋 Главная: {response_main}\n'
		f'      📋 Счётчики: {response_meters}\n'
		f'      📋 Закупки: {response_consumables}\n'
		f'      📋 Финансы продавцов: {response_finances_users}'
	)
	response_finances_staff = create_finance_staff_list()

	await message.edit_text(
		f'🔵 Создаю таблицы...\n'
		f'      📋 Главная: {response_main}\n'
		f'      📋 Счётчики: {response_meters}\n'
		f'      📋 Закупки: {response_consumables}\n'
		f'      📋 Финансы продавцов: {response_finances_users}\n'
		f'      📋 Финансы супервайзера: {response_finances_staff}'
	)
	update_info_shops()
	await bot.send_message(SERVICE_CHAT_ID, text='🟢 Бот активен')


async def on_shut_down_tasks(dp: Dispatcher):
	await bot.send_message(SERVICE_CHAT_ID, text='🔴 Бот выключен')


async def init_purchases():
	while True:
		time = time_now()
		current_day = time.weekday()
		current_hour = int(time.time().strftime('%H'))
		if current_day == 0 and 9 < current_hour < 15:
			for user_id in get_users_id():
				await bot.send_message(
					user_id,
					'Пришло время закупок. Как будете готовы, нажмите кнопку ниже',
					reply_markup=get_purchases_keyboard()
				)
				await bot.send_message(
					SERVICE_CHAT_ID,
					'📌 Разослал пользователям запросы на закупку.'
				)
				await sleep(55000)
		else:
			await sleep(3600)


@dp.callback_query_handler(lambda c: 'purchases_start' in c.data)
async def get_packages_large(callback_query: types.CallbackQuery):
	await callback_query.message.answer(f'Сколько единиц "Пакеты Большие" нужно?\nОтправь следующим сообщением')
	await UserState.packages_large.set()


@dp.message_handler(state=UserState.packages_large)
async def get_packing_bags(message: types.Message, state: FSMContext):
	await state.update_data(packages_large=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['packages_large']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Пакеты фасовочные" нужно?\nОтправь следующим сообщением')
	await UserState.packing_bags.set()


@dp.message_handler(state=UserState.packing_bags)
async def get_glasses(message: types.Message, state: FSMContext):
	await state.update_data(packing_bags=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['packing_bags']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Стаканы" нужно?\nОтправь следующим сообщением')
	await UserState.glasses.set()


@dp.message_handler(state=UserState.glasses)
async def get_containers_small(message: types.Message, state: FSMContext):
	await state.update_data(glasses=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['glasses']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Контейнеры маленькие" нужно?\nОтправь следующим сообщением')
	await UserState.containers_small.set()


@dp.message_handler(state=UserState.containers_small)
async def get_containers_large(message: types.Message, state: FSMContext):
	await state.update_data(containers_small=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['containers_small']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Контейнеры большие" нужно?\nОтправь следующим сообщением')
	await UserState.containers_large.set()


@dp.message_handler(state=UserState.containers_large)
async def get_cling_film(message: types.Message, state: FSMContext):
	await state.update_data(containers_large=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['containers_large']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Пищевая пленка" нужно?\nОтправь следующим сообщением')
	await UserState.cling_film.set()


@dp.message_handler(state=UserState.cling_film)
async def get_weight_tape(message: types.Message, state: FSMContext):
	await state.update_data(cling_film=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['cling_film']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Весовая Лента" нужно?\nОтправь следующим сообщением')
	await UserState.weight_tape.set()


@dp.message_handler(state=UserState.weight_tape)
async def get_receipt_tape(message: types.Message, state: FSMContext):
	await state.update_data(weight_tape=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['weight_tape']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Чековая Лента" нужно?\nОтправь следующим сообщением')
	await UserState.receipt_tape.set()


@dp.message_handler(state=UserState.receipt_tape)
async def get_soft_overhead(message: types.Message, state: FSMContext):
	await state.update_data(receipt_tape=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['receipt_tape']
	change_user_info(message.from_user.id, user_data)
	await message.answer('Принято!\nСколько единиц "Мягкие накладные" нужно?\nОтправь следующим сообщением')
	await UserState.soft_overhead.set()


@dp.message_handler(state=UserState.soft_overhead)
async def done_purchases(message: types.Message, state: FSMContext):
	await state.update_data(soft_overhead=message.text)
	data = await state.get_data()
	user_data = get_user_info(message.from_user.id)
	user_data['purchases']['packages_large'] = data['soft_overhead']
	change_user_info(message.from_user.id, user_data)
	await state.finish()
	update_consumables_list(message.from_user.id)
	await message.answer('Принято!\nВсе данные успешно внесены, можете продолжать работу.')


@dp.message_handler(commands='test')
async def test(message: types.Message):
	await message.answer(bot.id)


@dp.message_handler(commands=['clear'])
async def clear(message: types.Message):
	set_user_temple(message.from_user.id)
	await message.answer('Ваши данные очищены.')


@dp.message_handler(commands=['hard_clear'])
async def hard_clear(message: types.Message):
	if is_admin(message.chat.id):
		set_users_temple()
		set_staff_temple()
		await message.answer('Все данные очищены.')


@dp.message_handler(commands=['clear_staff'])
async def clear(message: types.Message):
	if is_admin(message.from_user.id):
		set_staff_temple()
		await message.answer('Данные очищены.')


if __name__ == '__main__':
	executor.start_polling(
		dp,
		skip_updates=True,
		on_startup=on_start_up_tasks,
		on_shutdown=on_shut_down_tasks,
	)
