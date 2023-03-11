import json

from table import *


def update_info_shops():
	try:
		with open('shops.json', 'r', encoding='utf-8') as shops:
			data = json.load(shops)

		all = get_shop_adresses(get_all=True)
		for idx, el in enumerate(all):
			if el.endswith(' (Дневная)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['day_only'][f'shop_{idx + 1}'] = el
			elif el.endswith(' (Дневная 24/7)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['day'][f'shop_{idx + 1}'] = el
			elif el.endswith(' (Ночная)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['night'][f'shop_{idx + 1}'] = el

		with open('shops.json', 'w') as shops:
			json.dump(data, shops)
	except json.JSONDecodeError:
		data = {'shop_addresses': {
			'day': {},
			'night': {},
			'day_only': {},
		}
		}
		all = get_shop_adresses(get_all=True)
		for idx, el in enumerate(all):
			if el.endswith(' (Дневная)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['day_only'][f'shop_{idx + 1}'] = el
			elif el.endswith(' (Дневная 24/7)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['day'][f'shop_{idx + 1}'] = el
			elif el.endswith(' (Ночная)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['night'][f'shop_{idx + 1}'] = el

		with open('shops.json', 'w') as shops:
			json.dump(data, shops)
	except KeyError:
		data = {'shop_addresses': {
			'day': {},
			'night': {},
			'day_only': {},
		}
		}
		all = get_shop_adresses(get_all=True)
		for idx, el in enumerate(all):
			if el.endswith(' (Дневная)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['day_only'][f'shop_{idx + 1}'] = el
			elif el.endswith(' (Дневная 24/7)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['day'][f'shop_{idx + 1}'] = el
			elif el.endswith(' (Ночная)'):
				end_idx = el.index(' (')
				el = el[:end_idx]
				data['shop_addresses']['night'][f'shop_{idx + 1}'] = el

		with open('shops.json', 'w') as shops:
			json.dump(data, shops)


def get_shop_id(shop_name: str, time: str):
	with open('shops.json', 'r', encoding='utf-8') as shops:
		data = json.load(shops)
		for key, value in data['shop_addresses'][time].items():
			if shop_name == value:
				return key
	return None
