from .conig import *
from bot_modules import *

import discord
from discord import app_commands
import sys
import os
import platform
import shutil
import asyncio
import requests
import datetime

def lprint(*text:str):
  """
  [現在時刻] text
  の形式でprint
  """
  text = map(str,text)
  datime_now = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M:%S')
  #logger.info(f"[{datime_now}]{' '.join(text)}")
  print(f"[{datime_now}]{' '.join(text)}")

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

global speakers
speakers:dict = {}

#必要ファイル、ディレクトリの作成
def setup():
  os.makedirs("./temp",exist_ok=True)
  if not os.path.exists("./dict.csv"):
    open("./dict.csv",encoding="utf-16",mode="w").write("")
  if not os.path.exists("./user.json"):
    open("./user.json",encoding="utf-8",mode="w").write("{}")

def get_speakers():
  global speakers
  with requests.Session() as session:
    resp = session.get(VOCIEVOX_SERVER+"speakers")
    resp_dict = resp.json()
    for i in resp_dict:
      #print(i["name"])
      speakers[i["name"]] = {}
      for s in i["styles"]:
        #print(s["id"],s["name"])
        speakers[i["name"]][s["name"]] = s["id"]


#起動時の処理
@client.event
async def on_ready():
  setup()
  lprint("BOTが起動しました。")
  lprint(f"{client.user.name} v{version}")

def generate(user_id:int, username:str, text:str):
  pass



#メッセージ受信時の処理
@client.event
async def on_message():
  pass


















client.run(BOT_TOKEN)

"""
try:
  asyncio.run(Client.start())
except KeyboardInterrupt:
  asyncio.run(Client.close())
"""

