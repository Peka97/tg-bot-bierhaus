from datetime import datetime, timedelta
import locale
import googleapiclient.errors
from pytz import timezone
from calendar import monthrange
import json
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from users import get_user_info, get_staff_fullname
from shops import *

with open('config.json', 'r', encoding='utf-8') as config:
    data = json.load(config)
    CREDENTIALS = data['CREDENTIALS_PATH']
    SPREADSHEET_ID_MAIN = data['SPREADSHEET_ID_MAIN']
    SPREADSHEET_ID_FINANCES = data['SPREADSHEET_ID_FINANCES']

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS,
    ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive']
)

httpAuth = credentials.authorize(httplib2.Http())
service = discovery.build('sheets', 'v4', http=httpAuth)

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

main_columns = {
    1: 'fullname',
    2: 'work_start',
    3: 'shop_status',
    4: 'cash',
    5: 'layout',
    6: 'cleaning',
    7: 'send_photo',
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

    current_year = datetime.now().astimezone(timezone('Europe/Saratov')).year()
    month = datetime.now().astimezone(timezone('Europe/Saratov')).month()
    return monthrange(current_year, month)[1]


def get_full_date():
    return datetime.now().astimezone(timezone('Europe/Saratov')).date().strftime("%d.%m.%Y")


def get_shop_name(shop_id: str, time: str):
    try:
        with open('shops.json', 'r', encoding='utf-8') as shops:
            data = json.load(shops)
            return data['shop_addresses'][time][shop_id]
    except KeyError:
        return None


def get_current_week_number():
    now = datetime.now().astimezone(timezone('Europe/Saratov'))
    return datetime.isocalendar(now).week // 12 + 1


def list_exist():
    """Проверяет наличие листа с текущей датой"""

    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    title = f'{current_month} Главная'
    sheets = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID_MAIN).execute().get('sheets')
    for sheet in sheets:
        if sheet['properties']['title'] == title:
            return True
    return False


def get_shop_adresses(time: str = None, get_all: bool = False) -> list:
    """Возвращает адреса магазинов"""

    response = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_MAIN,
        range=f'Main Pattern!A3:A22',
        majorDimension="COLUMNS",
    ).execute()
    if get_all:
        return [address for address in response['values'][0]]
    if time:
        return [address for address in response['values'][0] if time in str(address)]
    result = []
    for address in response['values'][0]:
        end_idx = address.index(' (')
        address = address[:end_idx]
        if address not in result:
            result.append(address)
    return result


def get_shop_row(shop_name: str, time: str):
    values = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_MAIN,
        range=f'Main Pattern!A3:A22',
        majorDimension="COLUMNS",
    ).execute()['values'][0]
    if time == 'day':
        addresses = [address[:-10]
                     for address in values if ' (Дневная)' in address]
    elif time == 'day_only':
        addresses = list(set(values) - set())
    else:
        addresses = [address[:-10]
                     for address in values if ' (Дневная)' in address]


# return values.index(shop_name)


def update_main_table_fields(user_id: int):
    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    title = f'{current_month} Главная'
    user_row = int(get_user_info(user_id)['row'])
    today = int(datetime.now().astimezone(
        timezone('Europe/Saratov')).strftime('%d'))
    cursor = 2 + 25 * (today - 1) + user_row
    column = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_MAIN,
        range=f'{title}!A{cursor}:O{cursor}',
        majorDimension="COLUMNS",
    ).execute()['values']

    for idx, value in main_columns.items():
        column[idx] = [get_user_info(user_id)[value]]

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_MAIN,
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


def update_meters_table_fields(user_id: int):
    try:
        today = int(datetime.now().astimezone(
            timezone('Europe/Saratov')).strftime('%d'))
        user_data = get_user_info(user_id)
        water = user_data['water_counter']
        light = user_data['light_counter']
        user_data = get_user_info(user_id)
        shop_name = get_shop_name(user_data['shop'], user_data['time'])
        current_month = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%m.%Y")
        title = f'{current_month} Счётчики'
        rows = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            range=f'{title}!A2:B26',
            majorDimension="ROWS",
        ).execute()['values']
        row_idx = None
        for idx, row in enumerate(rows):
            if row[0]:
                if shop_name in row[0]:
                    row_idx = idx
                    break
        meters = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            range=f'{title}!I2:AM26',
            majorDimension="ROWS",
        ).execute()['values']
        meters[row_idx][today - 1] = water
        meters[row_idx + 1][today - 1] = light

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'valueInputOption': 'USER_ENTERED',
                'data': [
                    {
                        'range': f'{title}!I2:AM26',
                        'majorDimension': 'ROWS',
                        'values': meters,
                    }
                ]
            }
        ).execute()
    except TypeError:
        user_data = get_user_info(user_id)
        print(
            f"Не удалось найти магазин {get_shop_name(user_data['shop'], user_data['time'])}")


def check_fields(user_id):
    try:
        current_month = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%m.%Y")
        title = f'{current_month} Главная'
        user_row = int(get_user_info(user_id)['row'])
        today = int(datetime.now().astimezone(
            timezone('Europe/Saratov')).strftime('%d'))
        cursor = 2 + 25 * (today - 1) + user_row

        column = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            range=f'{title}!A{cursor}:O{cursor}',
            majorDimension="ROWS",
        ).execute()['values']
        if column[0][1] != ' ':
            print(column[0][1])
            return column[0][1]
        return None
    except KeyError:
        return None


def get_sheet_id(name, spreadsheet_id: str):
    tables = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
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
    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    return f'{day:02}.{current_month}'


def create_main_list():
    try:
        current_month = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%m.%Y")
        title = f'{current_month} Главная'
        row_idx = 0
        column_idx = 0
        sheet_id = get_sheet_id(title, SPREADSHEET_ID_MAIN)
        if sheet_id is not None:
            return 'Таблица уже создана.'

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': {
                    'duplicateSheet': {
                        'sourceSheetId': 0,
                        'newSheetName': title,
                    },

                }
            }
        ).execute()

        sheet_id = get_sheet_id(title, SPREADSHEET_ID_MAIN)

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': sheet_id,
                                'hidden': False,
                                'index': 1,
                            },
                            'fields': 'hidden, index',
                        }
                    }
                ]
            }
        ).execute()

        for day in range(get_count_days() - 1):
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID_MAIN,
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
            spreadsheetId=SPREADSHEET_ID_MAIN,
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
        return 'Таблица уже создана.'

    return 'Таблица успешно создана.'


def create_meters_list():
    try:
        pattern_sheet_id = get_sheet_id('Meters Pattern', SPREADSHEET_ID_MAIN)
        current_month = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%m.%Y")
        date = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%B %Y")
        title = f'{current_month} Счётчики'

        sheet_id = get_sheet_id(title, SPREADSHEET_ID_MAIN)
        if sheet_id is not None:
            return 'Таблица уже создана.'

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': {
                    'duplicateSheet': {
                        'sourceSheetId': pattern_sheet_id,
                        'newSheetName': title,
                    },

                }
            }
        ).execute()

        sheet_id = get_sheet_id(title, SPREADSHEET_ID_MAIN)

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': sheet_id,
                                'hidden': False,
                                'index': 2,
                            },
                            'fields': 'hidden, index',
                        }
                    }
                ]
            }
        ).execute()

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': [
                    {
                        'findReplace':
                        {
                            "find": 'Месяц ГГГГ',
                            "replacement": date,
                            "matchCase": False,
                            "matchEntireCell": False,
                            "searchByRegex": False,
                            "includeFormulas": False,
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 2,
                                "startColumnIndex": 0,
                                "endColumnIndex": 2,
                            },
                        }
                    },

                ]
            }
        ).execute()

    except googleapiclient.errors.HttpError:
        return 'Таблица уже создана.'

    return 'Таблица успешно создана.'


def create_consumables_list():
    try:
        pattern_sheet_id = get_sheet_id(
            'Consumables Pattern', SPREADSHEET_ID_MAIN)
        current_month = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%m.%Y")
        date = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%d.%m.%Y")
        title = f'{current_month} Закупки'

        sheet_id = get_sheet_id(title, SPREADSHEET_ID_MAIN)
        if sheet_id is not None:
            return 'Таблица уже создана.'

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': {
                    'duplicateSheet': {
                        'sourceSheetId': pattern_sheet_id,
                        'newSheetName': title,
                    },

                }
            }
        ).execute()

        sheet_id = get_sheet_id(title, SPREADSHEET_ID_MAIN)

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': sheet_id,
                                'hidden': False,
                                'index': 3,
                            },
                            'fields': 'hidden, index',
                        }
                    }
                ]
            }
        ).execute()

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID_MAIN,
            body={
                'requests': [
                    {
                        'findReplace':
                        {
                            "find": 'ДД.ММ.ГГГГ',
                            "replacement": date,
                            "matchCase": False,
                            "matchEntireCell": False,
                            "searchByRegex": False,
                            "includeFormulas": False,
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 2,
                                "startColumnIndex": 0,
                                "endColumnIndex": 2,
                            },
                        }
                    },

                ]
            }
        ).execute()

    except googleapiclient.errors.HttpError:
        return 'Таблица уже создана.'

    return 'Таблица успешно создана.'


def update_consumables_list(user_id: int):
    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    column_idx = 0
    title = f'{current_month} Закупки'
    user_info = get_user_info(user_id)
    shop_name = get_shop_name(user_info['shop'], user_info['time'])

    values = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_MAIN,
        range=f'{title}!A1:M11',
        majorDimension="ROWS",
    ).execute()['values']

    addresses = values[1]
    shop_idx = addresses.index(shop_name)

    for row, count in zip(values[2:], user_info['purchases'].values()):
        row[shop_idx] = count

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_MAIN,
        body={
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': f'{title}!A1:M11',
                    'majorDimension': 'ROWS',
                    'values': values,
                }
            ]
        }
    ).execute()


def create_finance_user_list():
    try:
        pattern_sheet_id = get_sheet_id(
            'Finance User Pattern', SPREADSHEET_ID_FINANCES)
        addresses = get_shop_adresses()
        current_month = datetime.now().astimezone(
            timezone('Europe/Saratov')).date().strftime("%m.%Y")
        today = int(datetime.now().astimezone(
            timezone('Europe/Saratov')).strftime('%d'))
        for address in addresses:
            title = f'{current_month} {address}'
            row_idx = 0
            column_idx = 0

            sheet_id = get_sheet_id(title, SPREADSHEET_ID_FINANCES)

            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID_FINANCES,
                body={
                    'requests': {
                        'duplicateSheet': {
                            'sourceSheetId': pattern_sheet_id,
                            'newSheetName': title,
                        },

                    }
                }
            ).execute()

            sheet_id = get_sheet_id(title, SPREADSHEET_ID_FINANCES)

            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID_FINANCES,
                body={
                    'requests': [
                        {
                            'updateSheetProperties': {
                                'properties': {
                                    'sheetId': sheet_id,
                                    'hidden': False,
                                    'index': 1,
                                },
                                'fields': 'hidden, index',
                            }
                        }
                    ]
                }
            ).execute()

            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID_FINANCES,
                body={
                    'requests': [
                        {
                            'findReplace':
                            {
                                "find": 'ДД.ММ.ГГГГ',
                                "replacement": f'{today}.{current_month}',
                                "matchCase": False,
                                "matchEntireCell": False,
                                "searchByRegex": False,
                                "includeFormulas": False,
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": 0,
                                    "endRowIndex": 2,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 2,
                                },
                            }
                        },

                    ]
                }
            ).execute()

    except googleapiclient.errors.HttpError:
        return 'Таблица уже создана.'

    return 'Таблица успешно создана.'


def update_finance_user_list(user_id: int, comment: str, cash: dict):
    user_data = get_user_info(user_id)
    shop_id = user_data['shop']
    time = user_data['time']
    shop_address = get_shop_name(shop_id, time)
    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    current_time = datetime.now().astimezone(
        timezone('Europe/Saratov')).strftime("%d.%m.%y %H:%M")
    title = f'{current_month} {shop_address}'
    row_count = 1000

    tables = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        fields='sheets.properties'
    ).execute()['sheets']

    for table in tables:
        if table['properties']['title'] == title:
            row_count = table['properties']['gridProperties']['rowCount']
            break

    values = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        range=f'{title}!A1:E{row_count}',
        majorDimension="ROWS",
    ).execute()['values']

    if 'loss' in cash.keys():
        values.append([comment, cash['loss'], ' ', 'enter', current_time])
    else:
        values.append(
            [comment, ' ', cash['collection'], 'enter', current_time])

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        body={
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': f'{title}!A1:E{row_count}',
                    'majorDimension': 'ROWS',
                    'values': values,
                }
            ]
        }
    ).execute()


def create_finance_staff_list():
    pattern_sheet_id = get_sheet_id(
        'Finance Staff Pattern', SPREADSHEET_ID_FINANCES)
    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    title = f'{current_month} Финансы Супервайзер'

    sheet_id = get_sheet_id(title, SPREADSHEET_ID_FINANCES)
    if sheet_id:
        return 'Таблица уже создана.'

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        body={
            'requests': {
                'duplicateSheet': {
                    'sourceSheetId': pattern_sheet_id,
                    'newSheetName': title,
                },

            }
        }
    ).execute()

    sheet_id = get_sheet_id(title, SPREADSHEET_ID_FINANCES)

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        body={
            'requests': [
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet_id,
                            'hidden': False,
                            'index': 1,
                        },
                        'fields': 'hidden, index',
                    }
                }
            ]
        }
    ).execute()

    staff_fullname = get_staff_fullname()

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        body={
            'requests': [
                {
                    'findReplace':
                    {
                        "find": 'name',
                        "replacement": staff_fullname,
                        "matchCase": False,
                        "matchEntireCell": False,
                        "searchByRegex": False,
                        "includeFormulas": False,
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 2,
                            "startColumnIndex": 0,
                            "endColumnIndex": 2,
                        },
                    }
                },

            ]
        }
    ).execute()

    return 'Таблица создана.'


def update_finance_staff_list(comment: str, cash: dict = None):
    current_month = datetime.now().astimezone(
        timezone('Europe/Saratov')).date().strftime("%m.%Y")
    current_time = datetime.now().astimezone(
        timezone('Europe/Saratov')).strftime("%d.%m.%y %H:%M")
    title = f'{current_month} Финансы Супервайзер'
    row_count = 1000

    tables = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        fields='sheets.properties'
    ).execute()['sheets']

    for table in tables:
        if table['properties']['title'] == title:
            row_count = table['properties']['gridProperties']['rowCount']
            break

    values = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        range=f'{title}!A1:E{row_count}',
        majorDimension="ROWS",
    ).execute()['values']

    if 'Проверка фото-отчётов' in comment:
        values.append([comment, ' ', ' ', 'enter', current_time])
    elif 'income' in cash.keys():
        values.append([comment, cash['income'], ' ', 'enter', current_time])
    else:
        values.append([comment, ' ', cash['loss'], 'enter', current_time])

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID_FINANCES,
        body={
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': f'{title}!A1:E{row_count}',
                    'majorDimension': 'ROWS',
                    'values': values,
                }
            ]
        }
    ).execute()
