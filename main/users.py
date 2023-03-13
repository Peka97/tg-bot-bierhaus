import json


def set_user_temple(user_id):
    with open('users.json', 'r', encoding='utf-8') as users:
        data = json.load(users)

    data[f'{user_id}'] = {
        'row': '0',
        'time': "Н/Д",
        'shop': "Н/Д",
        'fullname': "Н/Д",
        'work_start': "Н/Д",
        'shop_status': "Н/Д",
        'cash': "Н/Д",
        'layout': "Н/Д",
        'cleaning': "Н/Д",
        'send_photo': "Н/Д",
        'expiration_date': "Н/Д",
        'work_done': "Н/Д",
        'revenue': "Н/Д",
        'terminal': "Н/Д",
        'collection': "Н/Д",
        'connected_kegs': "Н/Д",
        'full_kegs': "Н/Д",
        'purchases': {
                    'packages_large': 'Н/Д',
                    'packing_bags': 'Н/Д',
                    'glasses': 'Н/Д',
                    'containers_small': 'Н/Д',
                    'containers_large': 'Н/Д',
                    'cling_film': 'Н/Д',
                    'weight_tape': 'Н/Д',
                    'receipt_tape': 'Н/Д',
                    'soft_overhead': 'Н/Д',
        }
    }

    with open('users.json', 'w', encoding='utf-8') as users:
        json.dump(data, users)


def set_users_temple():
    try:
        with open('users.json', 'r', encoding='utf-8') as users:
            data = json.load(users)

        users = data.keys()
        for user in users:
            data[user] = {}

        with open('users.json', 'w', encoding='utf-8') as users:
            json.dump(data, users)
    except json.JSONDecodeError:
        with open('users.json', 'w', encoding='utf-8') as users:
            json.dump({'5503842748': {}}, users)


def set_staff_temple():
    with open('staff.json', 'w', encoding='utf-8') as staff:
        json.dump(
            {'admin': [840129933, 1387411715, 534430759], 'staff': {}}, staff)


def add_staff(user_id: int, fullname: str = None):
    with open('staff.json', 'r', encoding='utf-8') as staff:
        data = json.load(staff)
    with open('staff.json', 'w', encoding='utf-8') as staff:
        data['staff'][user_id] = fullname
        json.dump(data, staff)


def get_staff_fullname() -> str:
    try:
        with open('staff.json', 'r', encoding='utf-8') as staff:
            data = json.load(staff)
            return data['staff'].values()[-1]
    except AttributeError:
        return 'None'


def change_user_info(user_id: int, fields: dict):
    with open('users.json', 'r', encoding='utf-8') as users:
        data = json.load(users)

    user_info = data[str(user_id)]
    if 'purchases' in fields.keys():
        user_info['purchases'] = fields['purchases']
    else:
        for key, value in fields.items():
            user_info[key] = value

    with open('users.json', 'w', encoding='utf-8') as users:
        json.dump(data, users)


def get_user_info(user_id: int):
    with open('users.json', 'r', encoding='utf-8') as users:
        return json.load(users)[f'{user_id}']


def get_users_id():
    with open('users.json', 'r', encoding='utf-8') as users:
        return tuple(json.load(users).keys())
