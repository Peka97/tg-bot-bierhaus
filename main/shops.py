import json

from table import get_shop_adresses


def update_info_shops():
	try:
		with open('shops.json', 'r', encoding='utf-8') as shops:
			data = json.load(shops)

		addresses = get_shop_adresses()
		for idx, el in enumerate(addresses):
			data['shop_addresses'][f'shop_{idx + 1}'] = el

		with open('shops.json', 'w') as shops:
			json.dump(data, shops)
	except json.JSONDecodeError:
		data = {'shop_addresses': {}}
		addresses = get_shop_adresses()['values'][0]
		for idx, el in enumerate(addresses):
			data['shop_addresses'][f'shop_{idx + 1}'] = el

		with open('shops.json', 'w') as shops:
			json.dump(data, shops)


def get_shop_name(shop_id: str):
	with open('shops.json', 'r', encoding='uft-8') as shops:
		data = json.load(shops)
		for key, value in data['shop_addresses'].items():
			if shop_id == key:
				return value
	return None


def get_shop_id(shop_name: str):
	with open('shops.json', 'r', encoding='utf-8') as shops:
		data = json.load(shops)
		for key, value in data['shop_addresses'].items():
			if shop_name == value:
				return key
	return None
