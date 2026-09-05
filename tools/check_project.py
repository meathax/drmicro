"""Structural path/uniqueness audit; not Quartus elaboration or timing."""
import hashlib,json,pathlib,re,xml.etree.ElementTree as E,zipfile,zlib
from roms import R,manifest,load
def expand(path,seen=None):
 seen=set() if seen is None else seen
 result=[]
 for line in (R/path).read_text().splitlines():
  line=line.strip()
  if not line or line.startswith(('#','+define+')):continue
  if line.startswith('-f '):result+=expand(line[3:],seen)
  else:
   if line in seen:raise ValueError('Duplicate source '+line)
   seen.add(line);result.append(line)
 return result
def main():
 report={};sources=expand('sim/platform.f');mods={}
 defines=[line.removeprefix('+define+') for line in (R/'sim/core.f').read_text().splitlines() if line.startswith('+define+')]
 for define in defines:
  if not re.search(r'VERILOG_MACRO\s+"?'+re.escape(define)+r'"?\s*$',(R/'files.qip').read_text(),re.M):raise ValueError('Simulation macro missing from FPGA project: '+define)
 report['shared_defines']={'status':'PASS','defines':defines}
 for p in sources:
  text=(R/p).read_text();text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
  for mod in re.findall(r'\bmodule\s+(\w+)',text):
   if mod in mods:raise ValueError('Duplicate module '+mod)
   mods[mod]=p
  for inc in re.findall(r'`include\s+"([^"]+)"',text):
   if not any(x.exists() for x in [R/inc,(R/p).parent/inc]):raise ValueError('Missing include '+inc)
 report['explicit_source_lists']={'status':'PASS','files':len(sources),'modules':len(mods),'screen_rotate_definition':mods['screen_rotate']}
 # Recursively inspect Tcl/QIP references in both supported platform revisions.
 queue=[R/'Arcade-DrMicro.qsf'];seen=set();missing=[];optional=[]
 while queue:
  p=queue.pop()
  if p in seen:continue
  seen.add(p)
  for line in p.read_text(errors='replace').splitlines():
   if line.lstrip().startswith('#'):continue
   if 'pll_q [regexp' in line:
    queue.extend([R/'sys/pll_q17.qip',R/'sys/pll_q13.qip']);continue
   t=re.search(r'^source\s+(\S+)',line)
   if t:target=R/t[1];kind='source'
   else:
    t=re.search(r'-name\s+(\w+_FILE)\s+(.+)',line)
    if not t:continue
    kind,expr=t.groups()
    if kind not in ['QIP_FILE','VERILOG_FILE','SYSTEMVERILOG_FILE','VHDL_FILE','SDC_FILE','SOURCE_FILE','MISC_FILE','PRE_FLOW_SCRIPT_FILE','CDF_FILE']:continue
    if kind=='PRE_FLOW_SCRIPT_FILE':expr=expr.strip().strip('"').split(':',1)[-1]
    if '$::quartus(qip_path)' in expr:
     token=re.search(r'\$::quartus\(qip_path\)\s+"?([^"\] ]+)',expr)
     if not token:raise ValueError('Unparsed path '+line)
     target=p.parent/token[1]
    else:target=R/expr.strip().strip('"')
   if not target.exists():
    (optional if kind in ['MISC_FILE','CDF_FILE'] else missing).append(str(target.relative_to(R)))
   elif target.suffix in ('.qip','.tcl','.qsf'):queue.append(target)
 report['future_project_paths']={'status':'FAIL' if missing else 'PASS','missing':missing,'optional_upstream_misc':optional,'manifests_checked':len(seen),'quartus':'Separate explicit stage; see reports/quartus_map/fit/sta.json'}
 m=manifest();root=E.parse(R/'releases/Dr. Micro.mra').getroot();parts=root.findall("./rom[@index='0']/part")
 physical=[p for r in m['regions'] for p in r['parts']]
 assert [(p.get('name'),p.get('crc')) for p in parts]==[(p['name'],p['crc32']) for p in physical]
 report['mra_structure']={'status':'PASS','parts':len(parts),'dip_options':len(root.findall('./switches/dip'))}
 try:
  # Reconstruct directly from XML names, independently of the canonical packer.
  with zipfile.ZipFile(R/'drmicro.zip') as z:
   payload=b''
   for part in parts:
    b=z.read(part.get('name'));assert f'{zlib.crc32(b):08x}'==part.get('crc');payload+=b
  packed,_=load();assert payload==packed
  report['mra_payload']={'status':'PASS','length':len(payload),'md5':hashlib.md5(payload).hexdigest(),'sha256':hashlib.sha256(payload).hexdigest()}
 except FileNotFoundError:report['mra_payload']={'status':'BLOCKED','reason':'User ROM archive unavailable'}
 (R/'reports/project_checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 if missing:raise ValueError('Missing future-project inputs')
if __name__=='__main__':main()
