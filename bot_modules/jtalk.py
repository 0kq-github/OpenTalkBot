import subprocess

class jtalk:
  def __init__(self, path):
    self.path = path

  def generate(self, text:str, path, voice, style, speed, pitch):
      open_jtalk=[self.path]
      mech=['-x','./jtalk_dict/open_jtalk_dic_shift_jis-1.11']
      htsvoice=["-m",f"hts_voice/{voice}/{style}.htsvoice"]
      speed=['-r',str(speed)]
      pitch=["-fm",str(pitch)]
      jm=['-jm','1.0']
      outwav=['-ow',path]
      cmd=open_jtalk+htsvoice+speed+pitch+mech+jm+outwav
      c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
      c.stdin.write(text.encode(encoding="shift-jis"))
      c.stdin.close()
      c.wait()