"""Three complete independent ROM-download/boot runs, with deterministic checks."""
import hashlib,json
from dev import R,run_smoke

def main():
 scripts=['attract','cold_repeat1','cold_repeat2']
 for script in scripts:run_smoke(120,script)
 roots=[R/'reports/captures'/s for s in scripts]
 for n in [1,30,60,120]:
  for ext in ['ppm','pen','ram']:
   assert len({hashlib.sha256((p/f'frame_{n}.{ext}').read_bytes()).hexdigest() for p in roots})==1,(n,ext)
 results=[json.loads((p/'result.json').read_text()) for p in roots]
 for key in ['fetches','ram_writes','io_writes','nmi_events']:
  assert len({x[key] for x in results})==1,key
 result={'status':'PASS','runs':3,'frames_per_run':120,'evidence':'All captured RGB, raw pens, full RAM and execution counters identical across three independent process/cold-download boots.','binary_sha256':results[0]['binary_sha256']}
 (R/'reports/cold_boots.json').write_text(json.dumps(result,indent=2));print(result);return result
if __name__=='__main__':main()
