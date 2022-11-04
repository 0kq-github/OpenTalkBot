import requests
import time

class voiceroid:
  def __init__(self,address):
    self.address = address

  def generate(self,text,path,actor,mode,speed,pitch):
    with requests.Session() as session:
      for i in range(5):
        req = f"{self.address}generate?text={text}&speaker={actor}&mode={mode}&speed={speed}&pitch={pitch}"
        #req = urllib.parse.urlencode(req,encoding="shift-jis")
        s = session.get(req)
        with open(path,mode="wb") as f:
          f.write(s.content)
        if s.status_code == 200:
          break
        time.sleep(1)
    #sound_controller.convert_volume(path+".wav",0.7)