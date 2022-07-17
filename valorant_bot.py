import re
import os
import discord
import rso_request
import shop
import select_skin

client = discord.Client()

NIGHT_STORE_KEY = ['night', 'ナイト', 'ナイトストア', 'マーケット', 'ナイトマーケット', 'リサイクルショップ']
REGISTER_KEY = ['登録']
DEDELETE_KEY = ['削除']
CREATE_CHANNEL_KEY = ['ch create']
SELECT_VANDAL_SKIN = ['vandal', 'v', 'ヴァンダル']

@client.event
async def on_ready():
    print('connect')
    await client.change_presence(activity = discord.Game(name = 'valorant store', activity = discord.Streaming))

@client.event
async def on_message(message):
  if message.author.bot:
      return
  if client.user in message.mentions:
      global connectChannel
      if 'ばいばい' in message.content:
          await client.logout()
          return

      # RSO情報の登録
      elif re.sub('<@\d+>\s?', '', message.content) in REGISTER_KEY:
        text = 'ユーザー名とパスワードを空白区切りでどうぞ'
        dm_channel = message.author.dm_channel
        if dm_channel == None:
          dm_channel = await message.author.create_dm()
          while True:
            if dm_channel != None:
              break 
        await reply(dm_channel, text)
        return

      # RSO情報の削除
      elif re.sub('<@\d+>\s?', '', message.content) in DEDELETE_KEY:
        success = rso_request.delete_userdata(str(message.author.id))
        text = '削除に成功しました' if success else '削除に失敗しました'
        await reply(message.channel, text)

      # テキストチャンネルを作る
      elif re.sub('<@\d+>\s?', '', message.content) in CREATE_CHANNEL_KEY:
        await create_text_channel(message)

      # ヴァンダルのスキンを選ぶ  
      elif re.sub('<@\d+>\s?', '', message.content) in SELECT_VANDAL_SKIN:
        rso = await get_rso(message)
        user_skins = select_skin.get_user_skin_data(rso)

      # ストア情報を取ってくる
      else:
        rso = get_rso(message)
        skin_data = []
        if re.sub('<@\d+>\s?', '', message.content) in NIGHT_STORE_KEY:
          skin_data = shop.get_night_data(rso)
        else:
          skin_data = shop.get_skin_data(rso)
        if len(skin_data) == 0:
          text = 'ストア情報の取得に失敗しちゃった…'
          await reply(message.channel, text)
          return

        emojis = client.emojis
        emoji_VP = ''
        for emoji in emojis:
          if 'VP' == str(emoji.name):
            emoji_VP = ('<:VP:{0}>').format(emoji.id)
            break
        for skin in skin_data:
          await reply_embed(message.channel, '{0}　{1} {2}'.format(skin[0], emoji_VP, skin[1]), skin[2])

      #else:
      #  name = re.sub('<@!\d+>\s?', '', message.content)
      #  await message.guild.get_member(user_id = message.mentions[0].id).edit(nick = name)
      #  text = '名前を変更したぜ'
      #  await reply(message.channel, text)
      #  return
      
  # DMで発言があった場合
  elif message.channel == message.author.dm_channel:
      try:
        username, password = message.content.split()
      except:
        text = '空白区切りでユーザー名とパスワードですぞ'
        await reply(message.author.dm_channel, text)
        return

      rso = rso_request.get_rso_data(username, password)
      if rso == None:
        text = 'ログインに失敗したのでもう一回頼む'
        await reply(message.author.dm_channel, text)
      else:
        text = '認証に成功したのでbotがつかえるようになったよ！\n今できることはこれ ```・今日のショップ情報（メンション）\n・ナイトマーケット情報（メンション + night, ナイト, ナイトストア, マーケット, ナイトマーケット, リサイクルショップ）\n・登録した情報の削除（メンション + 削除）```'
        await reply(message.author.dm_channel, text)
        rso_request.set_userdata(message.author.id, username, password)
        return

# rsoデータの取得
async def get_rso(message):
  rso = rso_request.get_userdata(str(message.author.id))
  if rso == 'nodata':
    text = 'まずはメンションをつけて「登録」と発言してくれよな'
    await reply(message.channel, text)
  elif rso == 'multifactor':
    text = '二要素認証くんにはじかれちゃった…'
    await reply(message.channel, text)
  elif rso == None:
    text = '<@325308386985902090> たすけて'
    await reply(message.channel, text)
  else:
    return rso

# テキストチャンネルの作成
async def create_text_channel(message):
  #overwrites = {
  #  guild.default_role: discord.PermissionOverwrite(read_messages=False),
  #  guild.me: discord.PermissionOverwrite(read_messages=True)
  #}
  #channel = await guild.create_text_channel('聞き専', overwrites = overwrites)
  if message.channel.category != None:
    category = message.channel.category
    await category.create_text_channel('text_ch')
  else:
    guild = message.guild
    await guild.create_text_channel('text_ch')
  #await channel.set_permissions(message.author, read_messages = True, send_messages = True) 

# 返信
async def reply(channel, text, mention = None):
  if mention != None:
    await channel.send('{0} \n {1}'.format(mention, text), file = None)
  else:
    await channel.send(text)

# embedを使って送信
async def reply_embed(channel, title, image_url):
  embed = discord.Embed(title = title, color = 0x4169e1)
  #embed.set_thumbnail(url = image_url)
  embed.set_image(url = image_url)
  await channel.send(embed = embed)

client.run(os.environ['DISCORD_TOKEN'])

