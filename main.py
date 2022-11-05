import config
from bot_modules import *
from bot_modules import voiceroid_server
from bot_modules import voiceroid
from bot_modules import voicevox
from bot_modules import jtalk
from bot_modules import softalk

import discord
from discord import app_commands
from discord.ext import tasks
import os
import datetime
import aiofiles
import json
import asyncio
import requests
from threading import Thread
import logging
import csv
from typing import List
import re
import tarfile
import tqdm
import shutil
import xml.etree.ElementTree as ET
import subprocess

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = '%(asctime)s [%(levelname)s] %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(CustomFormatter())
logger.addHandler(stream_handler)


intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

dict_url = "https://altushost-swe.dl.sourceforge.net/project/open-jtalk/Dictionary/open_jtalk_dic-1.11/open_jtalk_dic_shift_jis-1.11.tar.gz"
mmdagent_url = "http://jaist.dl.sourceforge.net/project/mmdagent/MMDAgent_Example/MMDAgent_Example-1.8/MMDAgent_Example-1.8.zip"

global speakers
speakers:dict = {}
read_ch:int = 0
queue:list =[]
vv_list = [] #voicevox話者一覧
vc_list = [] #voiceroid話者一覧
jt_list = [] #openjtalk話者一覧
st_list = [] #softalk話者一覧
style_list = []
vv = voicevox.voicevox(config.VOICEVOX_SERVER)
vc = voiceroid.voiceroid(config.VOICEROID_SERVER)
jt = jtalk.jtalk(config.OPENJTALK_PATH)
st = softalk.softalk(config.SOFTALK_PATH)

#必要ファイル、ディレクトリの作成
def setup():
  os.makedirs("./temp",exist_ok=True)
  if not os.path.exists("./dict.csv"):
    open("./dict.csv",encoding="utf-16",mode="w").write("")
  if not os.path.exists("./user.json"):
    open("./user.json",encoding="utf-8",mode="w").write("{}")
  if os.path.exists("./open_jtalk.exe"):
    if not os.path.exists("./jtalk_dict/"):
      logger.info("OpenJtalkの辞書をダウンロード中...")
      file_size = int(requests.head(dict_url).headers["content-length"])
      session = requests.get(dict_url, stream=True)
      pbar = tqdm.tqdm(total=file_size, unit="B", unit_scale=True)
      with open("./download/dict.tar.gz",mode="wb") as f:
        for chunk in session.iter_content(chunk_size=1024):
          f.write(chunk)
          pbar.update(len(chunk))
        #f.write(session.content)
      t = tarfile.open(name="./download/dict.tar.gz")
      t.extractall("./jtalk_dict/")
    if not os.path.exists(config.HTS_DIR):
      logger.info("htsvoiceをダウンロード中...")
      file_size = int(requests.head(mmdagent_url).headers["content-length"])
      session = requests.get(mmdagent_url, stream=True)
      pbar = tqdm.tqdm(total=file_size, unit="B", unit_scale=True)
      with open("./download/mmdagent.zip",mode="wb") as f:
        for chunk in session.iter_content(chunk_size=1024):
          f.write(chunk)
          pbar.update(len(chunk))
        #f.write(session.content)
      shutil.unpack_archive("./download/mmdagent.zip","./temp/")
      shutil.copytree("./temp/MMDAgent_Example-1.8/Voice/","./hts_voice/")
      shutil.rmtree("./temp/MMDAgent_Example-1.8")

#話者の取得
def get_speakers():
  if os.path.exists(config.OPENJTALK_PATH):
    global jt_list
    jt_list = os.listdir(config.HTS_DIR)
    for i in jt_list:
      speakers[i] = {}
      for s in os.listdir(config.HTS_DIR+i):
        if s.endswith(".htsvoice"):
          s = s.replace(".htsvoice","")
          speakers[i][s] = s
    logger.info("OPENJTALKが読み込まれました")
    logger.info(" ".join(jt_list))
  else:
    logger.warning("OPENJTALKが見つかりませんでした")
  
  if os.path.exists(config.SOFTALK_PATH):
    global st_list
    subprocess.call([config.SOFTALK_PATH+"SofTalk.exe","/X:1","/Z:softalk.xml"])
    with open(config.SOFTALK_PATH+"softalk.xml",mode="r",encoding="shift_jis") as f:
      xml = f.read()
    xmlroot = ET.fromstring(text=xml)
    for child in xmlroot:
      #print(child.attrib["opt"],child.attrib["name"])
      if child.attrib["name"] == "AquesTalk":
        st_list.append(child.attrib["name"])
        speakers[child.attrib["name"]] = {}
        for ch in child:
          #print(" ",ch.attrib["opt"],ch.text)
          speakers[child.attrib["name"]]["AquesTalk_"+ch.text] = ch.attrib["opt"]
    logger.info("SOFTALKが読み込まれました")
    logger.info(" ".join(st_list))
  else:
    logger.warning("SOFTALKが見つかりませんでした")

  with requests.Session() as session:
    try:
      resp = session.get(config.VOICEVOX_SERVER+"speakers")
      resp_dict = resp.json()
      for i in resp_dict:
        speakers[i["name"]] = {}
        vv_list.append(i["name"])
        for s in i["styles"]:
          speakers[i["name"]][f"{i['name']}_{s['name']}"] = s["id"]
      logger.info("VOICEVOXが読み込まれました")
      logger.info(" ".join(vv_list))
    except Exception:
      logger.warning("VOICEVOXサーバーへの接続に失敗しました")

  with requests.Session() as session:
    try:
      resp = session.get(config.VOICEROID_SERVER+"speakers")
      resp_dict = resp.json()
      langs = {}
      for i in resp_dict["languages"]:
        langs[f"VOICEROID_{i}"] = i
      for i in resp_dict["speakers"]:
        speakers[i] = langs
        vc_list.append(i)
      logger.info("VOICEROIDが読み込まれました")
      logger.info(" ".join(vc_list))
    except Exception:
      logger.warning(f"VOICEROIDサーバーへの接続に失敗しました")
    
  for s in speakers.values():
    for i in s.keys():
      if not i in style_list:
        style_list.append(i)


#音声再生ループ
@tasks.loop(seconds=0.01)
async def send_audio():
  if queue:
    data = queue[0]
    datime = data[0]
    message:discord.Message = data[1]
    path = f"./temp/{datime}.wav"
    if message.guild.voice_client.is_playing():
      return
    elif not os.path.exists(path):
      return
    else:
      queue.pop(0)
      wav_source = discord.FFmpegPCMAudio(path, before_options="-guess_layout_max 0", options=f"-af equalizer=f=200:t=h:w=200")
      wav_source_half = discord.PCMVolumeTransformer(wav_source, volume=0.5)
      message.guild.voice_client.play(wav_source_half)
      



#起動時の処理
@client.event
async def on_ready():
  await tree.sync()
  if not speakers:
    logger.warning("話者が見つかりませんでした。音声エンジンの設定は適切ですか？")
  logger.info("BOTが起動しました!")
  logger.info(f"{client.user.name} v{version}")
  #logger.debug(speakers)

def dict_reader(path):
  with open(path,mode="r",encoding="utf-16",newline="") as f:
    u_dict = csv.reader(f)
    u_dict = {row[0]:row[1] for row in u_dict}
    return u_dict

def dict_writer(path, u_dict):
  with open(path,mode="w",encoding="utf-16",newline="") as f:
    writer = csv.writer(f)
    for k, v in u_dict.items():
      writer.writerow([k,v])


#辞書置換
def rep_dict(text):
  u_dict = dict_reader("./dict.csv")
  for i in u_dict:
    text = text.replace(i,u_dict[i])
  return text


#音声生成
def generate(datime,message:discord.Message,speak_conf:dict):
  #伏せ字
  spoiler = re.findall("\|\|.*\|\|",message.content)
  if spoiler:
    for i in spoiler:
      message.content = message.content.replace(i,"伏せ字")
  
  #メンション(メンバー)
  mention_member = re.findall("<@[!]?\d{18}>", message.content)
  for m in mention_member:
    m = m.replace("<","").replace(">","").replace("@","").replace("!","")
    for i in message.mentions:
      if not str(i.id) == m:
        continue
      mentioned_name = i.display_name
      message.content = message.content.replace(f"<@{m}>","@"+mentioned_name)
      message.content = message.content.replace(f"<@!{m}>","@"+mentioned_name)
  
  #メンション(チャンネル)
  mention_channel = re.findall("<#\d{18}>", message.content)
  for m in mention_channel:
    m = m.replace("<","").replace(">","").replace("#","").replace("!","")
    for i in message.channel_mentions:
      if not str(i.id) == m:
        continue
      mentioned_channel = i.name
      message.content = message.content.replace(f"<#{m}>", mentioned_channel)
  
  #絵文字
  emoji = re.findall("<.?:[^<^>]*:\d{18}>", message.content)
  if emoji:
    for i in emoji:
      emoji = re.search(":[^:]*:", i).group()
      message.content = message.content.replace(i,emoji)

  #URL
  message.content = re.sub("(https?):\/\/[^(\s　)]+","URL省略",message.content)

  name = rep_dict(message.author.display_name)
  text = rep_dict(message.content)
  logger.info(f"{message.author.display_name}: {message.content} >> {name}: {text}")
  path = f"./temp/{datime}.wav"
  if speak_conf["speaker"] in vv_list:
    vv.generate(f"{name} {text}", path+"_temp", speak_conf["style"], speak_conf["speed"], speak_conf["pitch"])
  if speak_conf["speaker"] in vc_list:
    vc.generate(f"{name} {text}", path+"_temp", speak_conf["speaker"], speak_conf["style"], speak_conf["speed"], speak_conf["pitch"])
  if speak_conf["speaker"] in jt_list:
    jt.generate(f"{name} {text}", path+"_temp", speak_conf["speaker"], speak_conf["style"], speak_conf["speed"], speak_conf["pitch"])
  if speak_conf["speaker"] in st_list:
    st.generate(f"{name} {text}", path+"_temp", speak_conf["speaker"], speak_conf["style"], speak_conf["speed"], speak_conf["pitch"])
  os.rename(path+"_temp",path)
  

async def trigger(message:discord.Message):
  async with aiofiles.open("./user.json",mode="r",encoding="utf-8") as f:
    data = await f.read()
    user_conf = json.loads(data)
    try:
      speak_conf = user_conf[str(message.author.id)]
    except:
      default_speaker = next(iter(speakers.keys()))
      speak_conf = {
        "speaker":default_speaker,
        "style":next(iter(speakers[default_speaker].values())),
        "speed":1,
        "pitch":0
      }
      user_conf[str(message.author.id)] = speak_conf
      async with aiofiles.open("./user.json",mode="w",encoding="utf-8") as f:
        await f.write(json.dumps(user_conf,indent=4))
  datime = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f')
  th = Thread(target=generate,args=(datime,message,speak_conf,))
  th.setDaemon(True)
  th.start()
  queue.append([datime, message, speak_conf])
  




#メッセージ受信時の処理
@client.event
async def on_message(message: discord.Message):
  global read_ch
  if message.author.bot:
    return
  if not message.channel.id == read_ch:
    return
  if client.voice_clients:
    await trigger(message)


class talk(app_commands.Group):
  help_msg = [
    "VCへ接続",
    "VCから切断",
    "辞書の追加",
    "辞書の削除",
    "話者の設定"
  ]

  @app_commands.command(name="help",description="help")
  async def help(self, itr:discord.Interaction):
    embed = discord.Embed(
      title="OpenTalkBotについて",
      description=f"**Version {version}**\n[リポジトリ](https://github.com/0kq-github/OpenTalkBot)",
      color=discord.Colour.blue()
      )
    embed.add_field(name="/talk start",value=self.help_msg[0])
    embed.add_field(name="/talk end",value=self.help_msg[1])
    embed.add_field(name="/talk add",value=self.help_msg[2])
    embed.add_field(name="/talk del",value=self.help_msg[3])
    embed.add_field(name="/talk set",value=self.help_msg[4])
    await itr.response.send_message(embed=embed)

  @app_commands.command(name="start",description=help_msg[0])
  async def start(self, itr:discord.Interaction):
    global read_ch
    try: 
      await itr.user.voice.channel.connect()
      embed = discord.Embed(
        title="接続しました！",
        description=f"<#{itr.channel.id}>\n\n:arrow_down:\n\n<#{itr.user.voice.channel.id}>",
        color=discord.Colour.green()
        )
      read_ch = itr.channel_id
    except Exception as e:
      embed = discord.Embed(
        title="接続に失敗しました",
        description=f"{e}",
        color=discord.Colour.red()
        )
    finally:
      await itr.response.send_message(embed=embed)
      os.makedirs("./temp/",exist_ok=True)
  
  @app_commands.command(name="end",description=help_msg[1])
  async def end(self, itr:discord.Interaction):
    try:
      await itr.guild.voice_client.disconnect()
      embed = discord.Embed(
        title="切断しました。",
        color=discord.Colour.green()
        )
      queue.clear()
    except Exception as e:
      embed = discord.Embed(
        title=f"エラーが発生しました",
        description=f"{e}",
        color=discord.Colour.red()
        )
    finally:
      await itr.response.send_message(embed=embed)
      shutil.rmtree("./temp/")


  @app_commands.command(name="add",description=help_msg[2])
  async def add(self, itr:discord.Interaction, 単語:str, 意味:str):
    word = 単語
    mean = 意味
    u_dict = dict_reader("./dict.csv")
    u_dict[word] = mean
    dict_writer("./dict.csv",u_dict)
    embed = discord.Embed(
      title="ユーザー辞書",
      description=f"**{word}** : **{mean}**",
      color=discord.Colour.green()
      )
    await itr.response.send_message(embed=embed)


  @app_commands.command(name="del",description=help_msg[3])
  async def delete(self, itr:discord.Interaction, 単語:str):
    word = 単語
    u_dict = dict_reader("./dict.csv")
    try:
      u_dict.pop(word)
      dict_writer("./dict.csv",u_dict)
      embed = discord.Embed(
        title="ユーザー辞書",
        description=f"削除 **{word}**",
        color=discord.Colour.blue()
        )
    except:
      embed = discord.Embed(
        title="ユーザー辞書",
        description=f"辞書が見つかりませんでした",
        color=discord.Colour.blue()
      )
    finally:
      await itr.response.send_message(embed=embed)
    
  
  async def actor_autocomplete(self,
    itr: discord.Interaction,
    current: str,
  ) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name=a, value=a) for a in vv_list+vc_list+jt_list+st_list]

  async def style_autocomplete(self,
    itr: discord.Interaction,
    current: str,
  ) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name=a, value=a) for a in style_list]
    
  v_suggest = "/talk set ずんだもん ずんだもん_ノーマル"
  @app_commands.command(name="set",description=help_msg[4])
  @app_commands.describe(話者=v_suggest,スタイル=v_suggest,速度=v_suggest,ピッチ=v_suggest)
  @app_commands.autocomplete(話者=actor_autocomplete,スタイル=style_autocomplete)
  async def setvoice(self, itr:discord.Interaction, 話者:str, スタイル:str = "default", 速度:float = 1.0, ピッチ:float = 100.0):
    speaker = 話者
    style = スタイル
    speed = 速度
    pitch = ピッチ

    if pitch == 100.0:
      if speaker in vv_list:
        pitch = 0.0
      if speaker in vc_list:
        pitch = 1.0
      if speaker in jt_list:
        pitch = 1.0
      if speaker in st_list:
        pitch = 1.0
    
    if style == "default":
      style = next(iter(speakers[speaker].keys()))

    async with aiofiles.open("./user.json",mode="r",encoding="utf-8") as f:
      data = await f.read()
      user_conf = json.loads(data)
      user_conf[str(itr.user.id)] = {
        "speaker":speaker,
        "style":speakers[speaker][style],
        "speed":speed,
        "pitch":pitch
      }

    async with aiofiles.open("./user.json",mode="w",encoding="utf-8") as f:
      await f.write(json.dumps(user_conf))
    
    embed = discord.Embed(title="話者設定",description=f"**{speaker}**\n{style}",color=discord.Colour.blue())
    embed.add_field(name="速度",value=f"{speed}")
    embed.add_field(name="ピッチ",value=f"{pitch}")
    await itr.response.send_message(embed=embed)

tree.add_command(talk())







#client.run(config.BOT_TOKEN)

async def start_bot():
  setup()
  
  th = Thread(target=voiceroid_server.run,args=(8100,logger,))
  th.setDaemon(True)
  th.start()

  get_speakers()

  

  async with client:
    await asyncio.gather(
      send_audio.start(),
      client.start(config.BOT_TOKEN)
    )

try:
  asyncio.run(start_bot())
except KeyboardInterrupt:
  logger.info("BOTを終了しています...")
  for c in client.voice_clients:
    asyncio.run(c.disconnect())
  asyncio.run(client.close())


