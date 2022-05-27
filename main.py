import config
from bot_modules import *
from bot_modules import voiceroid_server

import discord
from discord import app_commands
from discord.ext import tasks
import sys
import os
import platform
import shutil
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
speakers:dict = {"test":{"aaa":"bbb"}}
queue:list =[]
vv_list = []
vc_list = []

#必要ファイル、ディレクトリの作成
def setup():
  os.makedirs("./temp",exist_ok=True)
  if not os.path.exists("./dict.csv"):
    open("./dict.csv",encoding="utf-16",mode="w").write("")
  if not os.path.exists("./user.json"):
    open("./user.json",encoding="utf-8",mode="w").write("{}")

def get_speakers():
  with requests.Session() as session:
    try:
      resp = session.get(config.VOCIEVOX_SERVER+"speakers")
      resp_dict = resp.json()
      for i in resp_dict:
        #print(i["name"])
        speakers[i["name"]] = {}
        vv_list.append(i["name"])
        for s in i["styles"]:
          #print(s["id"],s["name"])
          speakers[i["name"]][f"VOICEVOX_{s['name']}"] = s["id"]
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
      

@tasks.loop(seconds=0.01)
async def send_audio():
  if queue:
    data = queue.pop(0)
    


#起動時の処理
@client.event
async def on_ready():
  if not speakers:
    logger.warning("話者が見つかりませんでした。VOICEVOXまたはVOICEROIDの設定は適切ですか？")
  logger.info("BOTが起動しました!")
  logger.info(f"{client.user.name} v{version}")


async def generate(user_id:int, username:str, text:str):
  async with aiofiles.open("./user.json",mode="r",encoding="utf-8") as f:
    data = await f.read()
    user_conf = json.loads(data)
    try:
      speak_conf = user_conf[str(user_id)]
    except:
      speak_conf = {
        "speaker":next(iter(speakers.keys())),
        "speed":1,
        "pitch":0
      }
      user_conf[str(user_id)] = speak_conf
      async with aiofiles.open("./user.json",mode="w",encoding="utf-8") as f:
        await f.write(json.dumps(user_conf))
    




#メッセージ受信時の処理
@client.event
async def on_message(message: discord.Message):
  if client.voice_clients:
    await generate(message.author.id,message.author.display_name,message.content)
  
  


















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
  asyncio.run(client.close())


