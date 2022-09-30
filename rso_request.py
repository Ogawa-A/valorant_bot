import os
import re
import ssl
import json
import gspread
import requests
import dataclasses
from Crypto.Cipher import AES
from urllib3 import PoolManager
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from oauth2client.service_account import ServiceAccountCredentials

@dataclasses.dataclass
class RSO:
  access_token : str
  entitlements_token : str
  user_id : str

class MultifactorException(Exception):
    pass

# 保存済みの情報のからRSO取得
def get_userdata(discord_id):
  sheet = get_spreadsheet()
  user_data = sheet.get_all_values()

  for data in user_data:
    if str(discord_id) in str(data[0]):
      # 複合化
      key = os.environ['AES_KEY'].encode()
      cipher = AES.new(key, AES.MODE_EAX, bytes.fromhex(data[3]))
      cipher_text = cipher.decrypt_and_verify(bytes.fromhex(data[1]), bytes.fromhex(data[2]))
      username, password = cipher_text.decode().split()

      print(('get spreadsheet: {0}, {1}').format(username, password))
      return get_rso_data(username, password)

  return 'nodata'

# ユーザー情報を保存する
def set_userdata(discord_id, username, password):
  sheet = get_spreadsheet()
  row_num = len(sheet.col_values(1))

  # 暗号化
  key = os.environ['AES_KEY'].encode()
  cipher = AES.new(key, AES.MODE_EAX)
  encrypt_text = '{0} {1}'.format(username, password).encode()
  cipher_text, tag = cipher.encrypt_and_digest(encrypt_text)

  sheet.update_cell(row_num + 1, 1, str(discord_id))
  sheet.update_cell(row_num + 1, 2, cipher_text.hex())
  sheet.update_cell(row_num + 1, 3, tag.hex())
  sheet.update_cell(row_num + 1, 4, cipher.nonce.hex())

# 保存したRSO情報を削除する
def delete_userdata(discord_id):
  sheet = get_spreadsheet()
  user_data = sheet.get_all_values()
  for i, data in enumerate(user_data):
    if discord_id == str(data[0]):
      sheet.delete_row(i+1)
      return True

  return False

def get_spreadsheet():
  json_dict = json.loads(os.environ['gcp-json'])
  scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
  credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
  gc = gspread.authorize(credentials)
  workbook = gc.open_by_key(os.environ['RSO_WORKBOOK_KEY'])
  sheet = workbook.get_worksheet(0)
  
  return sheet

# 認証情報を取得
def get_rso_data(username, password):
  print('get_rso_data')
  try:
    class SSLAdapter(HTTPAdapter):
              def init_poolmanager(self, connections, maxsize, block=False):
                  self.poolmanager = PoolManager(num_pools=connections,
                                              maxsize=maxsize,
                                              block=block,
                                              ssl_version=ssl.PROTOCOL_TLSv1_2)

    headers = OrderedDict({
              'User-Agent': 'RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)'
          })
    session = requests.session()
    session.mount('https://auth.riotgames.com/api/v1/authorization', SSLAdapter())
    session.headers = headers

    data = {
      'client_id': 'play-valorant-web-prod',
      'nonce': '1',
      'redirect_uri': 'https://playvalorant.com/opt_in',
      'response_type': 'token id_token',
    }
    r = session.post('https://auth.riotgames.com/api/v1/authorization', json=data, headers = headers)

    # access_tokenの取得
    data = {
      'type': 'auth',
      'username': username,
      'password': password,
      'language': 'ja-JP'
    }

    r = session.put('https://auth.riotgames.com/api/v1/authorization', json = data, headers = headers)
    pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    if r.json()['type'] == 'multifactor':
      raise MultifactorException
    data = pattern.findall(r.json()['response']['parameters']['uri'])[0]
    access_token = data[0]    
    print(('access_token: {0}').format(access_token))

    # entitlements_tokenの取得
    headers = {
      'Accept-Encoding': 'gzip, deflate, br',
      'Host': 'entitlements.auth.riotgames.com',
      'User-Agent': 'RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)',
      'Authorization': f'Bearer {access_token}',
    }
    r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
    entitlements_token = r.json()['entitlements_token']
    print(('entitlements_token: {0}').format(entitlements_token))


    # user_idの取得
    headers = {
              'Accept-Encoding': 'gzip, deflate, br',
              'Host': 'auth.riotgames.com',
              'User-Agent': 'RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)',
              'Authorization': f'Bearer {access_token}',
          }

    r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
    user_id = r.json()['sub']
    print(('user_id: {0}').format(user_id))


  except MultifactorException as e:
    return 'multifactor'
  except e:
    print(e)
    return None
  else: 
    return RSO(access_token, entitlements_token, user_id) 
  finally:
    session.close()
