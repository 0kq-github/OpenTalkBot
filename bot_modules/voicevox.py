import requests
import json

class voicevox:
  def __init__(self,address):
    self.address = address

  def generate(self,text, filename, speaker=1, speed=0, pitch=0):
    query_payload = {"text": text, "speaker": speaker}
    r = requests.post(self.address+"audio_query", 
                    params=query_payload, timeout=(10.0, 300.0))
    if r.status_code == 200:
        query_data = r.json()

    # synthesis
    synth_payload = {"speaker": speaker}    
    query_data["speedScale"] = speed
    query_data["pitchScale"] = pitch
    r = requests.post(self.address+"synthesis", params=synth_payload, 
                      data=json.dumps(query_data), timeout=(10.0, 300.0))
    if r.status_code == 200:
        with open(filename, "wb") as fp:
            fp.write(r.content)