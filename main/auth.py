import json
from json import JSONDecodeError

from users import set_staff_temple


def is_user(user_id: int):
	with open('users.json', 'r', encoding='utf-8') as users:
		data = json.load(users)
		return True if str(user_id) in data.keys() else False


def is_staff(user_id: int):
	with open('staff.json', 'r', encoding='utf-8') as staff:
		staffs = json.load(staff)['staff']
		return True if user_id in staffs else False


def is_admin(user_id: int):
	try:
		with open('staff.json', 'r', encoding='utf-8') as staff:
			admins = json.load(staff)['admin']
			return True if user_id in admins else False
	except (FileNotFoundError, JSONDecodeError, KeyError):
		set_staff_temple()
		with open('staff.json', 'r', encoding='utf-8') as staff:
			admins = json.load(staff)['admin']
			return True if user_id in admins else False
