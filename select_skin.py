import requests

def get_skin_data(wepon_type):
  r = requests.get('https://valorant-api.com/v1/weapons?language=ja-JP')
  master_skin_data = r.json()['data']

  display_names = []
  for wepon_data in master_skin_data:
    if wepon_data['displayName'] == wepon_type:     
      display_names.append(wepon_data['skins']['displayName'])

  return display_names
  