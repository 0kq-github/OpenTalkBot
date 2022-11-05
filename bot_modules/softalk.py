import time
import os
import subprocess

class softalk:
  def __init__(self,path):
    self.path = path
    if os.path.exists(path):
      os.makedirs(path+"temp",exist_ok=True)    

  def generate(self, text:str, path:str, voice, style, speed, pitch):
    speed = f"/S:{speed*100}"
    pitch = f"/O:{pitch*100}"
    word = f"/W:{text}"
    out = f"/R:{os.getcwd()}"+path[1:].replace('/','\\')
    if voice == "AquesTalk":
      voice = "/T:7"

    command = ["start",self.path.replace("/","\\")+"SofTalk.exe", "/X:1","/Q:5" , speed, pitch, voice, style, out, word]
    #print(command)
    subprocess.call(command,shell=True)
    while not os.path.exists(path):
      time.sleep(0.1)