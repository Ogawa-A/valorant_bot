import requests

# ショップデータを取得
def get_skin_data(rso):
  headers = {
    "X-Riot-Entitlements-JWT": rso.entitlements_token,
    "Authorization": f'Bearer {rso.access_token}',
  }

  # storeの取得
  url = 'https://pd.AP.a.pvp.net/store/v2/storefront/{0}'.format(rso.user_id)
  r = requests.get(url, headers=headers)

  try:
    store_skin_ids = r.json()['SkinsPanelLayout']['SingleItemOffers']
  except:
    print(url, '/n', r.json())
    return []

  # offerの取得
  url = 'https://pd.AP.a.pvp.net/store/v1/offers'
  r = requests.get(url, headers=headers)
  offers = r.json()['Offers']

  # masterの取得
  r = requests.get('https://valorant-api.com/v1/weapons/skins?language=ja-JP')
  master_skin_data = r.json()['data']
  offer_skin_data = []
  for id in store_skin_ids:
    display_name = ''
    display_icon = ''
    for skin_data in master_skin_data:
      if id in str(skin_data):
        print('skin_data: ', skin_data)
        display_name = skin_data['displayName']
        for level_data in skin_data['levels']:
          if level_data['levelItem'] == None: 
            display_icon = level_data['displayIcon']
            break
        if display_icon == None:
          display_icon = skin_data['displayIcon']
        break

    cost = ''
    for offer in offers:
      if id in str(offer):
        cost = list(offer['Cost'].values())[0]
        break

    offer_skin_data.append([display_name, cost, display_icon])

  return offer_skin_data

def get_night_data(rso):
  print('get_night_data')
  headers = {
    "X-Riot-Entitlements-JWT": rso.entitlements_token,
    "Authorization": f'Bearer {rso.access_token}',
  }

  # storeの取得
  url = 'https://pd.AP.a.pvp.net/store/v2/storefront/{0}'.format(rso.user_id)
  r = requests.get(url, headers=headers)

  print(r.json())
  try:
    night_offers = r.json()['BonusStore']['BonusStoreOffers']
  except:
    print(url, '/n', r.json())
    return []

  print(night_offers)

  # masterの取得
  r = requests.get('https://valorant-api.com/v1/weapons/skins?language=ja-JP')
  master_skin_data = r.json()['data']

  offer_skin_data = []
  for offer_data in night_offers:
    print('night_offers')
    display_name = ''
    display_icon = ''
    item_id = night_offers['Offer']['Rewards']['ItemID']

    for skin_data in master_skin_data:
      if item_id in str(skin_data):
        print('skin_data: ', skin_data)
        display_name = skin_data['displayName']
        for level_data in skin_data['levels']:
          if level_data['levelItem'] == None: 
            display_icon = level_data['displayIcon']
            break
        if display_icon == None:
          display_icon = skin_data['displayIcon']
        break

      base_cost = list(offer_data['Offer']['Cost']).values()[0]
      discount_per = offer_data['DiscountPercent']
      cost = list(offer_data['DiscountCosts']).values()[0]

      cost_text = '{0} ({1}:{2}% OFF)'.format(cost, base_cost, discount_per)
      offer_skin_data.append([display_name, cost_text, display_icon])
  

""" # 画像URLからndarray形式で画像を取得
def create_image_file(data):
  image = None
  image = np.asarray(bytearray(data.content), dtype = 'uint8')
  image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)

  return image

# スキン画像を作成
def create_skin_pict(skin_data):
  images = []
  for data in skin_data:
    images.append(create_image_file(requests.get(data[2])))

  # 指定サイズに収まるようにアス比を固定してリサイズ
  resize_images = []
  width = 512
  height = 200
  color = (255, 255, 255, 255)
  for image in images:
    h, w = image.shape[:2]
    aspect = w / h
    if width / height >= aspect:
      nh = height
      nw = round(nh * aspect)
    else:
      nw = width
      nh = round(nw / aspect)

    tmpimage = cv2.resize(image, dsize=(nw, nh), interpolation = cv2.INTER_AREA)

    # マージン追加時に黒くなってしまうため透過部分を一旦塗りつぶし
    #index = np.where(tmpimage[:, :, 3] == 0)
    #tmpimage[index] = color

    # 指定サイズになるようにマージンを追加
    image_height, image_width = tmpimage.shape[:2]
    margin_top = int((height + 20 - image_height) / 2)
    margin_bottom = margin_top if (height - image_height) % 2 == 0 else (margin_top + 1)
    margin_left = int((width + 10 - image_width) / 2)
    margin_right = margin_left if (width - image_width) % 2 == 0 else (margin_left + 1)

    #tmpimage = cv2.copyMakeBorder(tmpimage, margin_top, margin_bottom, margin_left, margin_right, cv2.BORDER_CONSTANT, value = color) 

    # 白色部分を透過する
    #tmpimage[:, :, 3] = np.where(np.all(tmpimage == 255, axis=-1), 0, 255)

    resize_images.append(tmpimage)

  result_image = []
  # 左上に武器名を入れる
  #font = get_font()
  #for data, image in zip(skin_data, images):
    #org = (0, 0)
    #result_image.append(cv2_putText(image, data[1], org, font, (225, 105, 65), 1))

  return resize_images

# フォントデータの取得
def get_font():
  path = './NotoSansJP-Regular.ttf'
  font_size = 5
  font = ImageFont.truetype(path, font_size)

  return font

# cv2で画像の上に日本語を載せられるようにする
def cv2_putText(img, text, org, font, color, mode = 0): 
    # 0（デフォ）＝cv2.putText()と同じく左下　1＝左上　2＝中央

    # テキスト描写域を取得
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (0,0)))
    text_w, text_h = dummy_draw.textsize(text, font = font)
    text_b = int(0.1 * text_h) # バグにより下にはみ出る分の対策

    # テキスト描写域の左上座標を取得（元画像の左上を原点とする）
    x, y = org
    offset_x = [0, 0, text_w//2]
    offset_y = [text_h, 0, (text_h+text_b)//2]
    x0 = x - offset_x[mode]
    y0 = y - offset_y[mode]
    img_h, img_w = img.shape[:2]

    # 画面外なら何もしない
    if not ((-text_w < x0 < img_w) and (-text_b-text_h < y0 < img_h)) :
        print ("out of bounds")
        return img

    # テキスト描写域の中で元画像がある領域の左上と右下（元画像の左上を原点とする）
    x1, y1 = max(x0, 0), max(y0, 0)
    x2, y2 = min(x0+text_w, img_w), min(y0+text_h+text_b, img_h)

    # テキスト描写域と同サイズの黒画像を作り、それの全部もしくは一部に元画像を貼る
    text_area = np.full((text_h+text_b,text_w,3), (0,0,0), dtype=np.uint8)
    text_area[y1-y0:y2-y0, x1-x0:x2-x0] = img[y1:y2, x1:x2]

    # それをPIL化し、フォントを指定してテキストを描写する（色変換なし）
    imgPIL = Image.fromarray(text_area)
    draw = ImageDraw.Draw(imgPIL)
    draw.text(xy = (0, 0), text = text, fill = color, font = font)

    # PIL画像をOpenCV画像に戻す（色変換なし）
    text_area = np.array(imgPIL, dtype = np.uint8)

    # 元画像の該当エリアを、文字が描写されたものに更新する
    img[y1:y2, x1:x2] = text_area[y1-y0:y2-y0, x1-x0:x2-x0]

    return img
"""