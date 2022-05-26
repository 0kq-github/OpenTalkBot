from .conig import *
from bot_modules import *

import discord
from discord import app_commands
import sys
import os
import platform
import shutil
import asyncio
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
Client = discord.Client(intents=intents)
tree = app_commands.CommandTree(Client)



@Client.event
async def on_ready():
  lprint("BOTが起動しました。")
  lprint(f"{Client.user.name} v{version}")















Client.run(BOT_TOKEN)

"""
try:
  asyncio.run(Client.start())
except KeyboardInterrupt:
  asyncio.run(Client.close())
"""

