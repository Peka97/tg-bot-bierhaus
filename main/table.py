from datetime import datetime, timedelta

import googleapiclient.errors
from pytz import timezone
from calendar import monthrange
import json
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from users import get_user_info

with open('config.json', 'r', encoding='utf-8') as config:
	data = json.load(config)
	CREDENTIALS = data['CREDENTIALS_PATH']
	SPREADSHEET_ID = data['SPREADSHEET_ID']

credentials = ServiceAccountCredentials.from_json_keyfile_name(
	CREDENTIALS,
	['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
)

httpAuth = credentials.authorize(httplib2.Http())
service = discovery.build('sheets', 'v4', http=httpAuth)

current_month = timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")
title = f'{current_month} Главная'

main_columns = {
	1: 'fullname',
	2: 'work_start',
	3: 'shop_status',
	4: 'layout',
	5: 'cleaning',
	6: 'send_photo',
	7: 'revision',
	8: 'expiration_date',
	9: 'work_done',
	10: 'revenue',
	11: 'terminal',
	12: 'collection',
	13: 'connected_kegs',
	14: 'full_kegs'
}


def get_count_days():
	"""Считает количество дней в текущем месяце текущего года"""

	current_year = timezone("Europe/Saratov").localize(datetime.now()).year
	month = timezone("Europe/Saratov").localize(datetime.now()).month
	return monthrange(current_year, month)[1]


def list_exist():
	"""Проверяет наличие листа с текущей датой"""

	sheets = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute().get('sheets')
	for sheet in sheets:
		if sheet['properties']['title'] == title:
			return True
	return False


def get_shop_adresses(time: str = None) -> list:
	"""Возвращает адреса магазинов"""

	response = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID,
		range=f'Main Pattern!A3:A22',
		majorDimension="COLUMNS",
	).execute()
	if time:
		return [address for address in response['values'][0] if time in str(address)]
	return [address for address in response['values'][0]]


def update_today_field(user_id: int):
	user_row = int(get_user_info(user_id)['row'])
	today = int(timezone('Europe/Saratov').localize(datetime.now()).strftime('%d'))
	cursor = 1 + 25 * (today - 1) + user_row - 1
	column = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID,
		range=f'{title}!A{cursor}:O{cursor}',
		majorDimension="COLUMNS",
	).execute()['values']

	for idx, value in main_columns.items():
		column[idx] = [get_user_info(user_id)[value]]

	service.spreadsheets().values().batchUpdate(
		spreadsheetId=SPREADSHEET_ID,
		body={
			'valueInputOption': 'USER_ENTERED',
			'data': [
				{
					'range': f'{title}!A{cursor}:O{cursor}',
					'majorDimension': 'COLUMNS',
					'values': column,
				}
			]
		}
	).execute()


def check_fields(user_id):
	try:
		user_row = int(get_user_info(user_id)['row'])
		today = int(timezone('Europe/Saratov').localize(datetime.now()).strftime('%d'))
		cursor = 1 + 25 * (today - 1) + user_row - 1

		column = service.spreadsheets().values().get(
			spreadsheetId=SPREADSHEET_ID,
			range=f'{title}!A{cursor}:O{cursor}',
			majorDimension="ROWS",
		).execute()['values']
		if column[0][1] != ' ':
			return column[0][1]
		return None
	except KeyError:
		return None


def get_sheet_id(name):
	tables = service.spreadsheets().get(
		spreadsheetId=SPREADSHEET_ID,
		fields='sheets.properties'
	).execute()['sheets']

	for table in tables:
		properties = tuple(table['properties'].values())
		sheet_id = properties[0]
		sheet_name = properties[1]
		if sheet_name == name:
			return sheet_id
	return None


def get_pattern_date(day):
	current_month = timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")
	return f'{day:02}.{current_month}'


def create_main_list():
	try:
		current_month = timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")
		title = f'{current_month} Главная'
		row_idx = 0
		column_idx = 0
		# Создаём дубликат по шаблону
		response = service.spreadsheets().batchUpdate(
			spreadsheetId=SPREADSHEET_ID,
			body={
				'requests': {
					'duplicateSheet': {
						'sourceSheetId': 0,
						'newSheetName': title,
					},

				}
			}
		).execute()

		sheet_id = get_sheet_id(title)

		# Раскрываем таблицу для пользователей
		response = service.spreadsheets().batchUpdate(
			spreadsheetId=SPREADSHEET_ID,
			body={
				'requests': [
					{
						'updateSheetProperties': {
							'properties': {
								'sheetId': sheet_id,
								'hidden': False,
							},
							'fields': 'hidden',
						}
					}
				]
			}
		).execute()

		# Кол-во дней на 1 меньше, т.к. в дубле уже есть 1 день.
		for day in range(get_count_days() - 1):
			response = service.spreadsheets().batchUpdate(
				spreadsheetId=SPREADSHEET_ID,
				body={
					'requests': [
						{
							'copyPaste': {
								"source": {
									"sheetId": sheet_id,
									"startRowIndex": row_idx,
									"endRowIndex": row_idx + 23,
									"startColumnIndex": column_idx,
									"endColumnIndex": column_idx + 15,
								},
								"destination": {
									"sheetId": sheet_id,
									"startRowIndex": row_idx + 25,
									"endRowIndex": row_idx + 47,
									"startColumnIndex": column_idx,
									"endColumnIndex": column_idx + 15,
								},
								"pasteType": 'PASTE_NORMAL',
								"pasteOrientation": 'NORMAL',
							}
						},
						{
							'findReplace':
								{
									"find": 'ДД.ММ.ГГГГ',
									"replacement": get_pattern_date(day + 1),
									"matchCase": False,
									"matchEntireCell": False,
									"searchByRegex": False,
									"includeFormulas": False,
									"range": {
										"sheetId": sheet_id,
										"startRowIndex": row_idx,
										"endRowIndex": row_idx + 2,
										"startColumnIndex": 0,
										"endColumnIndex": 2,
									},
								}
						},

					]
				}
			).execute()
			row_idx += 25
			day += 1

		response = service.spreadsheets().batchUpdate(
			spreadsheetId=SPREADSHEET_ID,
			body={
				'requests': [
					{
						'findReplace':
							{
								"find": 'ДД.ММ.ГГГГ',
								"replacement": get_pattern_date(get_count_days()),
								"matchCase": False,
								"matchEntireCell": False,
								"searchByRegex": False,
								"includeFormulas": False,
								"range": {
									"sheetId": sheet_id,
									"startRowIndex": row_idx,
									"endRowIndex": row_idx + 2,
									"startColumnIndex": 0,
									"endColumnIndex": 2,
								},
							}
					},

				]
			}
		).execute()

	except googleapiclient.errors.HttpError:
		return 'Таблица уже создана. Если она выглядит не правильно, то удалите её и запустите алгоритм заново.'

	return 'Таблица успешно создана.'
