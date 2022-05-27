import requests

class voiceroid:
  def __init__(self,address):
    self.address = address

  def generate(self,text,path,actor,mode,speed,pitch):
    with requests.Session() as session:
      req = f"{self.address}generate?text={text}&speaker={actor}&mode={mode}&speed={speed}&pitch={pitch}"
      #req = urllib.parse.urlencode(req,encoding="shift-jis")
      s = session.get(req)
      with open(path,mode="wb") as f:
        f.write(s.content)
    #sound_controller.convert_volume(path+".wav",0.7)