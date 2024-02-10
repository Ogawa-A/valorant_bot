import requests


# 最新のクライアント情報を取得
def get_client_version():
  r = requests.get('https://valorant-api.com/v1/version')
  version_data = r.json()['data']

  return version_data['riotClientBuild']

print(get_client_version())