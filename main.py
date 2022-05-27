import config
from bot_modules import *
from bot_modules import voiceroid_server
from bot_modules import voiceroid
from bot_modules import voicevox

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

global speakers
speakers:dict = {}
queue:list =[]
vv_list = []
vc_list = []
vv = voicevox.voicevox(config.VOICEVOX_SERVER)
vc = voiceroid.voiceroid(config.VOICEROID_SERVER)

#必要ファイル、ディレクトリの作成
def setup():
  os.makedirs("./temp",exist_ok=True)
  if not os.path.exists("./dict.csv"):
    open("./dict.csv",encoding="utf-16",mode="w").write("")
  if not os.path.exists("./user.json"):
    open("./user.json",encoding="utf-8",mode="w").write("{}")

#話者の取得
def get_speakers():
  with requests.Session() as session:
    try:
      resp = session.get(config.VOICEVOX_SERVER+"speakers")
      resp_dict = resp.json()
      for i in resp_dict:
        speakers[i["name"]] = {}
        vv_list.append(i["name"])
        for s in i["styles"]:
          speakers[i["name"]][f"VOICEVOX_{s['name']}"] = s["id"]
      logger.info("VOICEVOXが読み込まれました")
      logger.info(" ".join(vv_list))
    except requests.ConnectionError:
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
    except Exception:
      logger.warning("VOICEROIDサーバーへの接続に失敗しました")
      

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
      os.remove(path)
      


#起動時の処理
@client.event
async def on_ready():
  await tree.sync()
  if not speakers:
    logger.warning("話者が見つかりませんでした。VOICEVOXまたはVOICEROIDの設定は適切ですか？")
  logger.info("BOTが起動しました!")
  logger.info(f"{client.user.name} v{version}")

#辞書置換
def rep_dict(text):
  return text


#音声生成
def generate(datime,message:discord.Message,speak_conf:dict):
  name = rep_dict(message.author.display_name)
  text = rep_dict(message.content)
  path = f"./temp/{datime}.wav"
  if speak_conf["speaker"] in vv_list:
    vv.generate(f"{name} {text}",path+"_temp",speak_conf["style"],speak_conf["speed"],speak_conf["pitch"])
  if speak_conf["speaker"] in vc_list:
    vc.generate(f"{name} {text}",path+"_temp",speak_conf["speaker"],speak_conf["style"],speak_conf["speed"],speak_conf["ptich"])
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
  if message.author.bot:
    return
  if client.voice_clients:
    await trigger(message)
    logger.info(f"{message.author.display_name} >> {message.content}")


class talk(app_commands.Group):

  @app_commands.command(name="help")
  async def help(self, itr:discord.Interaction):
    embed = discord.Embed(title="OpenTalkBotについて",description="")
    await itr.response.send_message(embed=embed)

  @app_commands.command(name="start")
  async def start(self, itr:discord.Interaction):
    try: 
      await itr.user.voice.channel.connect()
      embed = discord.Embed(title="接続しました！",description=f"<#{itr.channel.id}>\n\n:arrow_down:\n\n<#{itr.user.voice.channel.id}>",color=discord.Colour.green())
    except:
      embed = discord.Embed(title="接続に失敗しました",color=discord.Colour.red())
    finally:
      await itr.response.send_message(embed=embed)
  
  @app_commands.command(name="end")
  async def end(self, itr:discord.Interaction):
    try:
      await itr.guild.voice_client.disconnect()
      embed = discord.Embed(title="切断しました。",color=discord.Colour.green())
    except Exception as e:
      embed = discord.Embed(title=f"エラーが発生しました {e}",color=discord.Colour.red())
    finally:
      await itr.response.send_message(embed=embed)

tree.add_command(talk())











#client.run(config.BOT_TOKEN)

async def start_bot():
  setup()
  
  th = Thread(target=voiceroid_server.run,args=(50021,logger,))
  th.setDaemon(True)
  th.start()

  get_speakers()

  send_audio.start()

  async with client:
    await client.start(config.BOT_TOKEN)

try:
  asyncio.run(start_bot())
except KeyboardInterrupt:
  logger.info("BOTを終了しています...")
  for c in client.voice_clients:
    asyncio.run(c.disconnect())
  asyncio.run(client.close())


