import json


def is_staff(user_id: int):
	with open('users.json', 'r', encoding='utf-8') as users:
		data = json.load(users)
		return True if str(user_id) in data.keys() else False
