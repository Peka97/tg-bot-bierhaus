import json


def set_user_temple(user_id):
	with open('users.json', 'r', encoding='utf-8') as users:
		data = json.load(users)

	data[f'{user_id}'] = {
		'row': '0',
		'time': "'-",
		'shop': "'-",
		'fullname': "'-",
		'work_start': "'-",
		'shop_status': "'-",
		'cash': "'-",
		'layout': "'-",
		'cleaning': "'-",
		'send_photo': "'-",
		'revision': "'-",
		'expiration_date': "'-",
		'work_done': "'-",
	}

	with open('users.json', 'w') as users:
		json.dump(data, users)


def change_user_info(user_id: int, fields: dict):
	with open('users.json', 'r', encoding='utf-8') as users:
		data = json.load(users)

	user_info = data[str(user_id)]
	for key, value in fields.items():
		user_info[key] = value

	with open('users.json', 'w') as users:
		json.dump(data, users)


def get_user_info(user_id: int):
	with open('users.json', 'r', encoding='utf-8') as users:
		return json.load(users)[f'{user_id}']
