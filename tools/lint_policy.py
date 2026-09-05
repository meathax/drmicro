"""Fail new structural warnings; retain exact, hash-bound platform waivers."""
import hashlib,json,re
from roms import R

STRUCTURAL={'LATCH','MULTIDRIVEN','UNOPTFLAT','WIDTHEXPAND','WIDTHTRUNC','IMPLICIT','UNDRIVEN','PINMISSING'}

def check(log):
 policy=json.loads((R/'sim/platform_waivers.json').read_text())
 allowed={x['warning']:x for x in policy['waivers']}
 used=[]
 for line in log.splitlines():
  line=line.replace('\\','/')
  match=re.match(r'%Warning-([^:]+): ([^:]+):',line)
  if not match or match[1] not in STRUCTURAL:continue
  item=allowed.get(line)
  if item is None:raise ValueError('Unreviewed structural platform warning: '+line)
  if hashlib.sha256((R/match[2]).read_bytes()).hexdigest()!=item['source_sha256']:raise ValueError('Waiver source changed: '+match[2])
  used.append(line)
 (R/'reports/platform_warning_review.json').write_text(json.dumps({'status':'PASS','waivers_used':len(used),'warnings':used,'policy':'sim/platform_waivers.json'},indent=2))
 print('PASS platform structural warning gate:',len(used),'exact hash-bound donor waivers')
