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
		'revision': "Н/Д",
		'expiration_date': "Н/Д",
		'work_done': "Н/Д",
		'revenue': "Н/Д",
		'terminal': "Н/Д",
		'collection': "Н/Д",
		'connected_kegs': "Н/Д",
		'full_kegs': "Н/Д",
	}

	with open('users.json', 'w', encoding='utf-8') as users:
		json.dump(data, users)


def set_staff_temple():
	with open('staff.json', 'w', encoding='utf-8') as staff:
		json.dump({'admin': [840129933, 1387411715], 'staff': [840129933, 1387411715], }, staff)


def add_staff(user_id: int):
	with open('staff.json', 'r', encoding='utf-8') as staff:
		data = json.load(staff)
	with open('staff.json', 'w', encoding='utf-8') as staff:
		data['staff'].append(user_id)
		json.dump(data, staff)


def change_user_info(user_id: int, fields: dict):
	with open('users.json', 'r', encoding='utf-8') as users:
		data = json.load(users)

	user_info = data[str(user_id)]
	for key, value in fields.items():
		user_info[key] = value

	with open('users.json', 'w', encoding='utf-8') as users:
		json.dump(data, users)


def get_user_info(user_id: int):
	with open('users.json', 'r', encoding='utf-8') as users:
		return json.load(users)[f'{user_id}']
