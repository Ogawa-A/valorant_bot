import os
import sys
import json
import asyncio
import aioconsole
import gspread
import requests
import dataclasses
import riot_auth
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

# 特定のメンバーのRSO取得
async def get_token(discord_id):
  user_data = get_userdata(discord_id)

  if not user_data:
    return 'nodata'
  
  rso = await get_member_token(user_data[0], user_data[1])
  return rso

# トークン系を取得
async def get_member_token(username, password):
    riot_auth.RiotAuth.RIOT_CLIENT_USER_AGENT = get_client_version()

    CREDS = username, password

    auth = riot_auth.RiotAuth()
    multifactor_status = await auth.authorize(*CREDS)

    while multifactor_status is True:
        # fetching the code must be asynchronous or blocking
        code = await aioconsole.ainput("Input 2fa code: ")
        try:
            await auth.authorize_mfa(code)
            break
        except riot_auth.RiotMultifactorError:
            print("Invalid 2fa code, please try again")


    print(f"Access Token Type: {auth.token_type}\n")
    print(f"Access Token: {auth.access_token}\n")
    print(f"Entitlements Token: {auth.entitlements_token}\n")
    print(f"User ID: {auth.user_id}")

    # region asyncio.run() bug workaround for Windows, remove below 3.8 and above 3.10.6
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # endregion

    return RSO(auth.access_token, auth.entitlements_token, auth.user_id) 

# スプレッドシートからユーザーデータを取得
def get_userdata(discord_id):
  sheet = get_spreadsheet()
  user_data = sheet.get_all_values()

  for data in user_data:
    if str(discord_id) in str(data[0]):
      # 複合化
      #key = os.environ['AES_KEY'].encode()
      key = os.getenv('AES_KEY').encode()
      cipher = AES.new(key, AES.MODE_EAX, bytes.fromhex(data[3]))
      cipher_text = cipher.decrypt_and_verify(bytes.fromhex(data[1]), bytes.fromhex(data[2]))
      username, password = cipher_text.decode().split()
      return username, password
  return False

# ユーザー情報を保存する
def set_userdata(discord_id, username, password):
  sheet = get_spreadsheet()
  row_num = len(sheet.col_values(1))

  # 暗号化
  #key = os.environ['AES_KEY'].encode()
  key = os.getenv('AES_KEY').encode()
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

# スプレッドシートへの接続
def get_spreadsheet():
  #json_dict = json.loads(os.environ['gcp-json'])
  json_dict = json.loads(os.getenv('gcp-json'))
  scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
  credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
  gc = gspread.authorize(credentials)
  #workbook = gc.open_by_key(os.environ['RSO_WORKBOOK_KEY'])
  workbook = gc.open_by_key(os.getenv('RSO_WORKBOOK_KEY'))
  sheet = workbook.get_worksheet(0)
  
  return sheet

# 最新のクライアント情報を取得
def get_client_version():
  r = requests.get('https://valorant-api.com/v1/version')
  version_data = r.json()['data']

  print(version_data)
  return version_data['riotClientBuild'] 

'''
# 認証情報を取得
def get_rso_data(username, password):
  client_version = get_client_version()

  try:
    class SSLAdapter(HTTPAdapter):
              def init_poolmanager(self, connections, maxsize, block=False):
                  self.poolmanager = PoolManager(num_pools=connections,
                                              maxsize=maxsize,
                                              block=block,
                                              ssl_version=ssl.PROTOCOL_TLSv1_2)

    headers = OrderedDict({
              'User-Agent': 'RiotClient/{0} rso-auth (Windows;10;;Professional, x64)'.format(client_version)
          })
    session = requests.session()
    session.mount('https://auth.riotgames.com/api/v1/authorization', SSLAdapter())
    session.headers = headers
    print(headers)

    data = {
      'client_id': 'play-valorant-web-prod',
      'nonce': '1',
      'redirect_uri': 'https://playvalorant.com/opt_in',
      'response_type': 'token id_token',
    }
    r = session.post('https://auth.riotgames.com/api/v1/authorization', json=data, headers = headers)

    # access_tokenの取得
    print('access_token')
    data = {
      'type': 'auth',
      'username': username,
      'password': password,
      'language': 'ja-JP'
    }

    r = session.put('https://auth.riotgames.com/api/v1/authorization', json = data, headers = headers)
    pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    print(r.json())
    if r.json()['type'] == 'multifactor':
      raise MultifactorException
    data = pattern.findall(r.json()['response']['parameters']['uri'])[0]
    access_token = data[0]    
    print(('access_token: {0}').format(access_token))

    # entitlements_tokenの取得
    headers = {
      'Accept-Encoding': 'gzip, deflate, br',
      'Host': 'entitlements.auth.riotgames.com',
      'User-Agent': 'RiotClient/{0} rso-auth (Windows;10;;Professional, x64)'.format(client_version),
      'User-Agent': 'ShooterGame/11 Windows/10.0.22621.1.768.64bit',
      'Authorization': f'Bearer {access_token}',
    }
    r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
    entitlements_token = r.json()['entitlements_token']
    print(('entitlements_token: {0}').format(entitlements_token))
                            
      
    # user_idの取得
    headers = {
              'Accept-Encoding': 'gzip, deflate, br',
              'Host': 'auth.riotgames.com',
              'User-Agent': 'RiotClient/{0} rso-auth (Windows;10;;Professional, x64)'.format(client_version),
              'Authorization': f'Bearer {access_token}',
          }

    r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
    user_id = r.json()['sub']
    print(('user_id: {0}').format(user_id))


  except MultifactorException as e:
    return 'multifactor'
  except:
    print('None')
    return None
  else: 
    return RSO(access_token, entitlements_token, user_id) 
  finally:
    session.close()

'''