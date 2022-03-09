import os
import re
import ssl
import json
import gspread
import requests
import dataclasses
from urllib3 import PoolManager
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from oauth2client.service_account import ServiceAccountCredentials

@dataclasses.dataclass
class RSO:
  access_token : str
  entitlements_token : str
  user_id : str

# 保存済みのRSO情報の取得
def get_local_RSO(discord_id):
  sheet = get_spreadsheet()
  ros_data = sheet.get_all_values()
  
  for rso in ros_data:
    if str(discord_id) in str(rso[0]):
      return RSO(rso[1], rso[2], rso[3])

  return None

# RSO情報を保存する
def set_local_rso(discord_id, rso, username, password):
  sheet = get_spreadsheet()
  row_num = len(sheet.col_values(1))
  sheet.update_cell(row_num + 1, 1, str(discord_id))
  sheet.update_cell(row_num + 1, 2, rso.access_token)
  sheet.update_cell(row_num + 1, 3, rso.entitlements_token)
  sheet.update_cell(row_num + 1, 4, rso.user_id)
  #sheet.update_cell(row_num + 1, 5, username)
  #sheet.update_cell(row_num + 1, 6, password)


# 保存したRSO情報を削除する
def delete_local_rso(discord_id):
  sheet = get_spreadsheet()
  rso_data = sheet.get_all_values()
  for i, rso in enumerate(rso_data):
    if discord_id == str(rso[0]):
      sheet.delete_row(i)
      return True

  return False


def get_spreadsheet():
  json_dict = json.loads(os.environ['gcp-json'])
  scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
  credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
  gc = gspread.authorize(credentials)
  workbook = gc.open_by_key(os.environ['WORKBOOK_KEY'])
  sheet = workbook.get_worksheet(0)
  
  return sheet

# 認証情報を取得
def get_rso_data(username, password):
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
    #print(r.text)

    # access_tokenの取得
    data = {
      'type': 'auth',
      'username': username,
      'password': password,
      'language': 'ja-JP'
    }

    r = session.put('https://auth.riotgames.com/api/v1/authorization', json = data, headers = headers)
    pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    data = pattern.findall(r.json()['response']['parameters']['uri'])[0]
    access_token = data[0]
    #print('Access Token: ' + access_token)

    # entitlements_tokenの取得
    headers = {
      'Accept-Encoding': 'gzip, deflate, br',
      'Host': 'entitlements.auth.riotgames.com',
      'User-Agent': 'RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)',
      'Authorization': f'Bearer {access_token}',
    }
    r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
    entitlements_token = r.json()['entitlements_token']
    #print('Entitlements Token: ' + entitlements_token)  

    # user_idの取得
    headers = {
              'Accept-Encoding': 'gzip, deflate, br',
              'Host': 'auth.riotgames.com',
              'User-Agent': 'RiotClient/43.0.1.4195386.4190634 rso-auth (Windows;10;;Professional, x64)',
              'Authorization': f'Bearer {access_token}',
          }

    r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
    user_id = r.json()['sub']

  except:
    session.close()
    return None
  else:
    session.close()
    return RSO(access_token, entitlements_token, user_id)
