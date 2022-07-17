import requests

def get_skin_data(rso):
  headers = {
    "X-Riot-Entitlements-JWT": rso.entitlements_token,
    "Authorization": f'Bearer {rso.access_token}',
  }

  # スキン情報の取得
  url = 'https://pd.AP.a.pvp.net/personalization/v2/players/{0}/playerloadout'.format(rso.user_id)
  r = requests.get(url, headers=headers)

  try:
    user_skins = r.json()['Guns']
  except:
    print(url, '/n', r.json())
    return []

  print(user_skins)
  