from datetime import datetime
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


def get_count_days():
	"""Считает количество дней в текущем месяце текущего года"""

	current_year = timezone("Europe/Saratov").localize(datetime.now()).year
	month = timezone("Europe/Saratov").localize(datetime.now()).month
	return monthrange(current_year, month)[1]


def fill_today_list():
	"""Подтягивает данные с шаблона листа и заполняет ими лист текущего месяца"""
	column_idx = 1
	row_idx = 23
	values = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID,
		range=f'Pattern!A1:J23',
		majorDimension="COLUMNS",
	).execute()['values']

	for day in range(get_count_days()):
		values[0][0] = timezone("Europe/Saratov").localize(datetime.now()).strftime(f'{day + 1}.%m.%Y')
		values[4][-1] = '=СУММ(E3:E22)'
		service.spreadsheets().values().batchUpdate(
			spreadsheetId=SPREADSHEET_ID,
			body={
				'valueInputOption': 'USER_ENTERED',
				'data': [
					{
						'range': f'{timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")}!A{column_idx}:K{row_idx}',
						'majorDimension': 'COLUMNS',
						'values': values
					}
				]
			}
		).execute()

		column_idx += 25
		row_idx += 25
	return None


def list_exist():
	"""Проверяет наличие листа с текущей датой"""

	sheets = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute().get('sheets')
	for sheet in sheets:
		if sheet['properties']['title'] == timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y"):
			return True
	return False


def create_list():
	"""Создаёт новый лист с текущей датой"""

	response = service.spreadsheets().batchUpdate(
		spreadsheetId=SPREADSHEET_ID,
		body={
			'requests': {
				'addSheet': {
					'properties': {
						'title': f'{timezone("Europe/Saratov").localize(datetime.now()).strftime("%m.%Y")}'
					}
				}
			}
		}
	).execute()
	return response


def get_shop_adresses(time: str = None):
	"""Возвращает адреса магазинов"""

	response = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID,
		range=f'Pattern!A3:A22',
		majorDimension="COLUMNS",
	).execute()
	if time:
		response = [address for address in response['values'][0] if time in str(address)]
	return response


def update_today_field(user_id: int):
	user_row = int(get_user_info(user_id)['row'])
	today = int(timezone('Europe/Saratov').localize(datetime.now()).strftime('%d'))
	cursor = 1 + 25 * (today - 1) + user_row - 1
	column = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID,
		range=f'{timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")}!A{cursor}:K{cursor}',
		majorDimension="COLUMNS",
	).execute()['values']

	for idx in range(len(column)):
		if idx == 1:
			column[idx] = [get_user_info(user_id)['fullname']]
		elif idx == 2:
			column[idx] = [get_user_info(user_id)['work_start']]
		elif idx == 3:
			column[idx] = [get_user_info(user_id)['shop_status']]
		elif idx == 4:
			column[idx] = [get_user_info(user_id)['cash']]
		elif idx == 5:
			column[idx] = [get_user_info(user_id)['layout']]
		elif idx == 6:
			column[idx] = [get_user_info(user_id)['cleaning']]
		elif idx == 7:
			column[idx] = [get_user_info(user_id)['send_photo']]
		elif idx == 8:
			column[idx] = [get_user_info(user_id)['revision']]
		elif idx == 9:
			column[idx] = [get_user_info(user_id)['work_done']]

	service.spreadsheets().values().batchUpdate(
		spreadsheetId=SPREADSHEET_ID,
		body={
			'valueInputOption': 'USER_ENTERED',
			'data': [
				{
					'range': f'{timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")}!A{cursor}:K{cursor}',
					'majorDimension': 'COLUMNS',
					'values': column,
				}
			]
		}
	).execute()


def check_fields(user_id):
	user_row = int(get_user_info(user_id)['row'])
	today = int(timezone('Europe/Saratov').localize(datetime.now()).strftime('%d'))
	cursor = 1 + 25 * (today - 1) + user_row - 1

	column = service.spreadsheets().values().get(
		spreadsheetId=SPREADSHEET_ID,
		range=f'{timezone("Europe/Saratov").localize(datetime.now()).date().strftime("%m.%Y")}!A{cursor}:K{cursor}',
		majorDimension="ROWS",
	).execute()['values']

	try:
		if column[0][1] != '  ':
			return column[0][1]
		return None
	except KeyError:
		return None
