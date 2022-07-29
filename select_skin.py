import requests
import random

# スキンデータの取得
def get_skin_data(wepon_type):
  r = requests.get('https://valorant-api.com/v1/weapons?language=ja-JP')
  master_skin_data = r.json()['data']

  display_names = []
  for wepon_data in master_skin_data:
    if wepon_data['displayName'] == wepon_type:
        for skin in wepon_data['skins']:
            display_names.append(skin['displayName'])

  return display_names

# くじ引き
def lottery_skin(wepon_type):
  skins = get_skin_data(wepon_type)

  return random.choice(skins)