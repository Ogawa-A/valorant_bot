
import os
import json
import random
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials



# スキンデータの取得
def get_skin_data(wepon_type):
  battlepath_skin_teir_uuid = '12683d76-48d7-84a3-4e09-6985794f0445'
  r = requests.get('https://valorant-api.com/v1/weapons?language=ja-JP')
  master_skin_data = r.json()['data']

  battlepath_skins = []
  store_skins = []
  for wepon_data in master_skin_data:
    if wepon_data['displayName'] == wepon_type:
        for skin in wepon_data['skins']:
          if skin['contentTierUuid'] == battlepath_skin_teir_uuid:
            battlepath_skins.append(skin['displayName'])
          else:
            store_skins.append(skin['displayName'])

  return sorted(battlepath_skins), sorted(store_skins)

# くじ引き
def lottery_skin(wepon_type, is_include_battlepath = False):
  battlepath_skins, store_skins = get_skin_data(wepon_type)

  if is_include_battlepath:
    store_skins.extend(battlepath_skins)

  return random.choice(store_skins)


  return random.choice(skins)