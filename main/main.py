import logging
import json
import re
from datetime import datetime
from pytz import timezone
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from auth import is_user, is_staff, is_admin
from users import *
from shops import update_info_shops, get_shop_name
from table import list_exist, update_today_field, check_fields, create_main_list
from keyboards import *

with open('config.json', 'r', encoding='utf-8') as config:
	data = json.load(config)
	API_TOKEN = data['TOKEN']

# logging.basicConfig(filename="bot_log.log", filemode="a", level=logging.ERROR)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


def time_now():
	return timezone('Europe/Saratov').localize(datetime.now()).strftime('%H:%M')


class UserState(StatesGroup):
	time = State()
	shop = State()
	fullname = State()
	shop_status = State()
	is_work = State()
	cash = State()
	loss_count = State()
	loss_cause = State()
	revenue = State()
	terminal = State()
	collection = State()
	water_counter = State()
	light_counter = State()
	connected_kegs = State()
	full_kegs = State()


class StaffState(StatesGroup):
	collection_count = State()
	collection_shop = State()
	collection_cause = State()
	loss_count = State()
	loss_cause = State()
	income_count = State()
	income_cause = State()


class AdminState(StatesGroup):
	user_id = State()


cash_re = re.compile(r"\d+")


async def set_menu(role: str, chat_id: int):
	scope = types.BotCommandScopeChat(chat_id)
	if role == 'admin':
		await bot.set_my_commands(
			[
				types.BotCommand('/start', 'Начать'),
				types.BotCommand('/help', 'Помощь'),
			],
			scope=scope
		)
	elif role == 'staff':
		await bot.set_my_commands(
			[
				types.BotCommand('/start', 'Начать смену'),
				types.BotCommand('/help', 'Помощь'),
				types.BotCommand('/loss', 'Расход'),
				types.BotCommand('/income', 'Приход'),
				types.BotCommand('/collection', 'Инкассация'),
			],
			scope=scope
		)
	elif role == 'user':
		await bot.set_my_commands(
			[
				types.BotCommand('/start', 'Начать смену'),
				types.BotCommand('/help', 'Помощь'),
				types.BotCommand('/loss', 'Расход'),
				types.BotCommand('/collection', 'Инкассация'),
			],
			scope=scope
		)


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
		await set_menu('staff', message.from_user.id)
		await message.reply(
			text='Здравствуйте! Вы зашли под учетной записью супервайзера',
			reply_markup=get_start_keyboard()
		)
	elif is_user(message.from_user.id):
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
		await callback_query.message.answer('Принято! Переход в главное меню', reply_markup=get_staff_keyboard())


@dp.callback_query_handler(lambda c: 'cancel' in c.data, state='*')
async def back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
	if state:
		await state.finish()
	if is_admin(callback_query.message.chat.id):
		await callback_query.message.answer('Возврат в главное меню', reply_markup=get_admin_keyboard())
	elif is_staff(callback_query.message.chat.id):
		await callback_query.message.answer('Возврат в главное меню', reply_markup=get_staff_keyboard())
	elif is_user(callback_query.message.chat.id):
		await callback_query.message.answer('Возврат в главное меню')


@dp.message_handler(text='Инкассация')
async def collection_get_count(message: types.Message):
	if is_staff(message.chat.id):
		await message.answer(
			'Укажите сумму, которую забрали из кассы цифрами в следующем сообщении или нажмите "Отменить"',
			reply_markup=get_cancel_keyboard()
		)
		await StaffState.collection_count.set()


@dp.message_handler(state=StaffState.collection_count)
async def collection_get_shop(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(collection_count=message.text)
		data = await state.get_data()
		await message.answer(
			'Напишите адрес магазина, откуда забрали деньги или нажмите "Отменить"',
			reply_markup=get_cancel_keyboard()
		)
		await StaffState.collection_shop.set()


@dp.message_handler(state=StaffState.collection_shop)
async def collection_get_cause(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(collection_shop=message.text)
		data = await state.get_data()
		await message.answer('Принято!', reply_markup=get_staff_keyboard())
		await state.finish()


@dp.message_handler(text='Расход', state='*')
async def get_loss(message: types.Message, state: FSMContext):
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
			'Отправьте причину расхода следующим сообщением или нажмите "Отменить"',
			reply_markup=get_cancel_keyboard()
		)
		await StaffState.loss_cause.set()
	elif is_staff(message.chat.id):
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
		await message.answer('Принято!', reply_markup=get_staff_keyboard())
	elif is_user(message.chat.id):
		await state.update_data(loss_cause=message.text)
		data = await state.get_data()
		await message.answer('Принято!', reply_markup=get_staff_keyboard())
	await state.finish()


@dp.callback_query_handler(lambda c: 'check_staff' in c.data)
async def staff_start(callback_query: types.CallbackQuery):
	if is_admin(callback_query.message.chat.id) or is_staff(callback_query.message.chat.id):
		await callback_query.message.answer(
			text='Здравствуйте! Вы зашли под учетной записью супервайзера',
			reply_markup=get_start_keyboard()
		)


@dp.message_handler(text='Приход')
async def get_income(message: types.Message):
	if is_staff(message.chat.id):
		pass


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
async def add_staff_func(message: types.Message, state: FSMContext):
	await state.update_data(user_id=message.text)
	data = await state.get_data()
	add_staff(int(data['user_id']))
	await message.reply('Пользователь добавлен в список администраторов')


@dp.callback_query_handler(lambda c: c.data.startswith('shop_'), state='*')
async def send_fullname(callback_query: types.CallbackQuery, state: FSMContext):
	if is_user(callback_query.message.chat.id):
		await state.update_data(shop=callback_query.data)
		data = await state.get_data()
		change_user_info(
			callback_query.message.chat.id,
			{
				"shop": data['shop'],
				"row": f'{int(data["shop"].lstrip("shop_")) + 2}'
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
			update_today_field(message.from_user.id)
			await state.finish()
			await message.answer('Принято!')
			await message.answer(
				f'Начинаем смену, {fullname}!\nОткрой смену в 1С и нажми на кнопку ниже',
				reply_markup=get_work_start_keyboard()
			)


@dp.callback_query_handler(lambda c: c.data.startswith('work_start'))
async def send_work_start(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		data = {'work_start': f"{time_now()}"}
		change_user_info(callback_query.message.chat.id, data)
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			f'Визуально в магазине/на складе все целое и все в порядке?',
			reply_markup=get_shop_status_keyboard()
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
async def send_cash_no(message: types.Message):
	if is_user(message.chat.id):
		shop_status = message.text
		change_user_info(message.chat.id, {"shop_status": shop_status})
		update_today_field(message.chat.id)
		await message.answer('Принято!', reply_markup=get_user_keyboard())
		await message.answer(
			f'Прими денежные средства и отправь сумму следующим сообщением.'
		)
		await UserState.cash.set()


@dp.callback_query_handler(lambda c: c.data.startswith('status_shop_yes'))
async def send_cash_yes(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"shop_status": "Без особенностей"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			f'Прими денежные средства и отправь сумму следующим сообщением.'
		)
		await UserState.cash.set()


@dp.message_handler(state=UserState.cash)
async def send_layout(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(cash=message.text)
		data = await state.get_data()
		if cash_re.match(data['cash']):
			data['cash'] = ''.join([el for el in data['cash'] if el.isdigit()])
			change_user_info(message.chat.id, data)
			update_today_field(message.chat.id)
			await state.finish()
			await message.answer(f'{message.text} принято!', reply_markup=get_user_keyboard())
			await message.answer(
				'Разложи товар, по окончанию нажми на кнопку "Товар разложен"',
				reply_markup=get_layout_keyboard()
			)
		else:
			await message.reply(
				f'Ввод "{data["cash"]}" недопустим. Введите число только с помощью цифр',
				reply_markup=get_user_keyboard()
			)
			await UserState.cash.set()


@dp.callback_query_handler(lambda c: c.data.startswith('layout_yes'))
async def send_cleaning(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"layout": "'+"})
		update_today_field(callback_query.message.chat.id)
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
		update_today_field(callback_query.message.chat.id)
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
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'После проверки ты получишь до 10 баллов, Продолжай! (нажать на кнопку "Продолжить")',
			reply_markup=get_continue_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('continue'))
async def send_revision(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Проведи локальную ревизию и нажми на кнопку "Ревизия проведена"',
			reply_markup=get_revision_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('revision_yes'))
async def send_expiration_date(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"revision": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Проверь сроки годности товаров и нажать на кнопку "Срок годности проверен"',
			reply_markup=get_expiration_date_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('expiration_date_yes'))
async def send_work_done(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"expiration_date": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.answer('Принято!', reply_markup=get_user_keyboard())
		await callback_query.message.answer(
			'Закрой смену в 1С и нажми на кнопку "Закрыла смену 1С"',
			reply_markup=get_work_done_keyboard(),
		)


@dp.callback_query_handler(lambda c: 'is_work_no' in c.data)
async def send_revenue_or_exit(callback_query: types.CallbackQuery):
	if is_user(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"work_done": f"{time_now()}"})
		update_today_field(callback_query.message.chat.id)
		if get_user_info(callback_query.message.chat.id)['time'] == 'only_day':
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
		change_user_info(message.chat.id, {'revenue': data['revenue']})
		update_today_field(message.chat.id)
		await message.answer('Принято!\n Теперь напиши выручку с терминала цифрами в следующем сообщении')
		await UserState.terminal.set()


@dp.message_handler(state=UserState.terminal)
async def send_collection_or_exit(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(terminal=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'terminal': data['terminal']})
		update_today_field(message.chat.id)
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
		change_user_info(message.chat.id, {'collection': data['collection']})
		update_today_field(message.chat.id)
		await message.answer('Принято! Введите показания счётчика воды')
		await UserState.water_counter.set()


@dp.message_handler(state=UserState.water_counter)
async def send_light_counter(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(water_counter=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'water_counter': data['water_counter']})
		update_today_field(message.chat.id)
		await message.answer('Принято! Введите показания счётчика света')
		await UserState.light_counter.set()


@dp.message_handler(state=UserState.light_counter)
async def send_connected_kegs(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(light_counter=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'light_counter': data['light_counter']})
		update_today_field(message.chat.id)
		await message.answer('Принято! Введите количество подключенных кег')
		await UserState.connected_kegs.set()


@dp.message_handler(state=UserState.connected_kegs)
async def send_full_kegs(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(connected_kegs=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'connected_kegs': data['connected_kegs']})
		update_today_field(message.chat.id)
		await message.answer('Принято! Введите количество полных кег')
		await UserState.full_kegs.set()


@dp.message_handler(state=UserState.full_kegs)
async def send_cleaning(message: types.Message, state: FSMContext):
	if is_user(message.chat.id):
		await state.update_data(full_kegs=message.text)
		data = await state.get_data()
		await state.finish()
		change_user_info(message.chat.id, {'full_kegs': data['full_kegs']})
		update_today_field(message.chat.id)
		set_user_temple(message.from_user.id)
		await message.answer('Принято!', reply_markup=get_user_keyboard())
		await message.answer(
			'На этом всё. Хорошего отдыха!\nКак выйдешь на смену - просто нажми "Начать смену"',
			reply_markup=get_start_keyboard(),
		)


@dp.message_handler(commands=['clear'])
async def test(message: types.Message):
	set_user_temple(message.from_user.id)
	await message.answer('Ваши данные очищены')


if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)
