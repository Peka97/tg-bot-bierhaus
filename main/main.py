import logging
import json
import re
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from auth import is_staff
from users import change_user_info, set_user_temple, get_user_info
from shops import update_info_shops, get_shop_name
from table import list_exist, create_list, fill_today_list, update_today_field, check_fields
from keyboards import *

with open('config.json', 'r', encoding='utf-8') as config:
	data = json.load(config)
	API_TOKEN = data['TOKEN']

logging.basicConfig(filename="bot_log.log", filemode="a", level=logging.ERROR)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class UserState(StatesGroup):
	time = State()
	shop = State()
	fullname = State()
	shop_status = State()
	is_work = State()
	cash = State()


cash_re = re.compile(r"\d+")


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	if is_staff(message.from_user.id):
		set_user_temple(message.from_user.id)
		if not list_exist():
			await message.reply('В БД нет листа с текущей датой. Начинаю его создавать, ожидайте около 15 секунд')
			create_list()
			fill_today_list()
		update_info_shops()
		await message.reply("Здравствуйте! Выберете свою смену:", reply_markup=get_time_keyboard())
		await UserState.fullname.set()
	else:
		await message.reply("Тебя нет в моём списке. Обратись к руководству.")


@dp.callback_query_handler(lambda c: c.data.startswith('day') or c.data.startswith('night'), state='*')
async def send_shops(callback_query: types.CallbackQuery, state: FSMContext):
	if is_staff(callback_query.message.chat.id):
		await state.update_data(time=callback_query.data)
		data = await state.get_data()
		change_user_info(callback_query.message.chat.id, {"time": data['time']})
		await callback_query.message.reply(
			'Принято. Выберите номер магазина:',
			reply_markup=get_shops_keyboard(data['time'])
		)


@dp.callback_query_handler(lambda c: c.data.startswith('shop_'), state='*')
async def send_fullname(callback_query: types.CallbackQuery, state: FSMContext):
	if is_staff(callback_query.message.chat.id):
		await state.update_data(shop=callback_query.data)
		data = await state.get_data()
		change_user_info(
			callback_query.message.chat.id,
			{
				"shop": data['shop'],
				"row": f'{int(data["shop"].lstrip("shop_")) + 2}'
			}
		)
		await callback_query.message.reply('Принято! Напишите своё ФИО:')
		await UserState.fullname.set()


@dp.message_handler(state=UserState.fullname)
async def send_fullname(message: types.Message, state: FSMContext):
	if is_staff(message.from_user.id):
		await state.update_data(fullname=message.text)
		data = await state.get_data()
		fullname = data['fullname']
		if check_fields(message.chat.id) is not None:
			await message.reply(
				f'В этом магазине уже работает {check_fields(message.chat.id)}\n'
				'Выберите другой:',
				reply_markup=get_shops_keyboard(data['time'])
			)
		else:
			change_user_info(message.from_user.id, data)
			update_today_field(message.from_user.id)
			await state.finish()
			await message.reply(
				f'Начинаем смену, {fullname}!\nОткрой смену в 1С и нажми на кнопку ниже',
				reply_markup=get_work_start_keyboard()
			)


@dp.callback_query_handler(lambda c: c.data.startswith('work_start'))
async def send_work_start(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, data)
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			f'Визуально в магазине/на складе все целое и все в порядке?',
			reply_markup=get_shop_status_keyboard()
		)


@dp.callback_query_handler(lambda c: c.data.startswith('status_shop_no'))
async def send_status_shop_comment(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		await callback_query.message.reply(
			f'Прокомментируй недочет состояния магазина в ответном сообщении и постарайся его устранить. Позже во всём'
			' разберемся'
		)
		await UserState.shop_status.set()


@dp.message_handler(state=UserState.shop_status)
async def send_cash_no(message: types.Message):
	if is_staff(message.chat.id):
		shop_status = message.text
		change_user_info(message.chat.id, {"shop_status": shop_status})
		update_today_field(message.chat.id)
		await message.reply(
			f'Ок!\nПрими денежные средства, в поле ввода напиши цифрами сколько вышло и отправь мне.'
		)
		await UserState.cash.set()


@dp.callback_query_handler(lambda c: c.data.startswith('status_shop_yes'))
async def send_cash_yes(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"shop_status": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			f'Ок!\nПрими денежные средства, в поле ввода напиши цифрами сколько вышло и отправь мне.'
		)
		await UserState.cash.set()


@dp.message_handler(state=UserState.cash)
async def send_layout(message: types.Message, state: FSMContext):
	if is_staff(message.chat.id):
		await state.update_data(cash=message.text)
		data = await state.get_data()
		if cash_re.match(data['cash']):
			data['cash'] = ''.join([el for el in data['cash'] if el.isdigit()])
			change_user_info(message.chat.id, data)
			update_today_field(message.chat.id)
			await state.finish()
			await message.reply(
				f'{message.text} принято!\nРазложи товар, по окончанию нажми на кнопку "Товар разложен"',
				reply_markup=get_layout_keyboard()
			)
		else:
			await message.reply(
				f'Ввод "{data["cash"]}" недопустим. Введите число только с помощью цифр'
			)
			await UserState.cash.set()


@dp.callback_query_handler(lambda c: c.data.startswith('layout_yes'))
async def send_cleaning(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"layout": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			'Уберись в помещении (протирка кранов, протирка всех поверхностей, проверить чистоту окон и стёкол витрин)'
			'и нажми на кнопку " Все чисто"',
			reply_markup=get_cleaning_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('cleaning_yes'))
async def send_photo(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"cleaning": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			'Отправь Фото отчет в группу с Админом до 11.00 (Электроэнергия, Раскладка, Фасад магазина, лист смены кег)'
			'и нажми кнопку отправила,',
			reply_markup=get_send_photo_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('send_photo_yes'))
async def send_continue(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"send_photo": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			'Супер! После проверки ты получишь до 10 баллов, Продолжай! (нажать на кнопку "Продолжить")',
			reply_markup=get_continue_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('continue'))
async def send_revision(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		await callback_query.message.reply(
			'Провести локальную ревизию и нажать на кнопку "ревизия проведена"',
			reply_markup=get_revision_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('revision_yes'))
async def send_expiration_date(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"revision": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			'Контроль срока годности товара и нажать на кнопку " Срок годности проверен"',
			reply_markup=get_expiration_date_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('expiration_date_yes'))
async def send_work_done(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"expiration_date": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			'Закрыть смену в 1С и нажать на кнопку "Закрыла смену 1с"',
			reply_markup=get_work_done_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('is_work_no'))
async def send_exit(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		change_user_info(callback_query.message.chat.id, {"work_done": "'+"})
		update_today_field(callback_query.message.chat.id)
		await callback_query.message.reply(
			f'Отличная смена {get_user_info(callback_query.message.chat.id)["fullname"]}, завтра будет еще круче!',
			reply_markup=get_done_keyboard(),
		)


@dp.callback_query_handler(lambda c: c.data.startswith('exit'))
async def send_cleaning(callback_query: types.CallbackQuery):
	if is_staff(callback_query.message.chat.id):
		set_user_temple(callback_query.message.from_user.id)
		await callback_query.message.reply(
			'Хорошего отдыха! Как выйдешь на работу, просто нажми на /start и начнём',
			reply_markup=None,
		)


if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)
