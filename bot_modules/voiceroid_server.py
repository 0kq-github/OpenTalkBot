import pyvcroid2
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import uvicorn
import sys
import json

app = FastAPI(debug=False)



@app.get("/generate", response_class=FileResponse)
def generate(text:str,speaker:str,mode:str,speed:float,pitch:float):
  with pyvcroid2.VcRoid2() as vc:
    vc.loadLanguage(mode)
      
    # Load Voice
    vc.loadVoice(speaker)

    # Set parameters
    vc.param.volume = 1
    vc.param.speed = speed
    vc.param.pitch = pitch
    vc.param.emphasis = 1
    vc.param.pauseMiddle = 100
    vc.param.pauseLong = 100
    vc.param.pauseSentence = 100
    vc.param.masterVolume = 1

    for i in text:
      try:
        i.encode("shift-jis")
      except:
        text = text.replace(i,"")


    text = text.replace("\ufe0f","")
    speech, tts_events = vc.textToSpeech(text)
    return Response(content=speech,media_type="audio/wav")

@app.get("/speakers")
def speakers():
    with pyvcroid2.VcRoid2() as vc:
      resp = {
        "speakers":vc.listVoices(),
        "languages":vc.listLanguages()
        }
      return resp

def run(port:int, logger = None):
  try:
    pyvcroid2.VcRoid2()
    uvicorn.run(app=app,host="0.0.0.0",port=port,log_level="critical",access_log=False)
  except:
    msg = "VOICEROIDサーバーの初期化に失敗しました。VOICEROID2はインストールされていますか？"
    if logger:
      logger.warning(msg)
    else:
      print(msg)

if __name__ == "__main__":
  run(int(sys.argv[1]))