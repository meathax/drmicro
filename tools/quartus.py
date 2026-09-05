"""Explicit Quartus A&S, fit and timing stages; no assembler or programming."""
import csv,hashlib,json,os,pathlib,re,shutil,subprocess,time
from dev import R,ENV,run

def run_stage(args,filename):
 print('RUN',' '.join(map(str,args)),flush=True)
 path=R/'reports'/filename
 with path.open('w',encoding='utf-8') as log:
  process=subprocess.run(list(map(str,args)),env=ENV,stdout=log,stderr=subprocess.STDOUT)
 text=path.read_text(errors='replace');print(text[-2500:],flush=True)
 if process.returncode:raise RuntimeError('Quartus exited '+str(process.returncode)+'; see '+filename)
 return text

def executable(stage):
 base=pathlib.Path(os.environ.get('QUARTUS_ROOTDIR','C:/intelFPGA_lite/17.0/quartus'))
 for folder in ['bin64','bin']:
  p=base/folder/('quartus_'+stage+('.exe' if os.name=='nt' else ''))
  if p.is_file():return p
 raise FileNotFoundError('Quartus executable unavailable under '+str(base))

def identity():
 paths=[]
 for folder in ['rtl','sys']:
  paths += [p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ['.v','.sv','.vhd','.vh','.qip','.sdc','.tcl','.hex','.mif']]
 paths += [R/p for p in ['Arcade-DrMicro.sv','Arcade-DrMicro.qsf','Arcade-DrMicro.qpf','Arcade-DrMicro.sdc','files.qip','build_id.v']]
 hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
 return dict(files=hashes,sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest())

def main(stage='map'):
 if stage not in ['map','fit','sta']:raise ValueError('Unsupported Quartus stage')
 version=run([executable('sh'),'--version'],'quartus_version.log').strip()
 if stage=='map':run([executable('sh'),'-t','sys/build_id.tcl','quartus_sh','Arcade-DrMicro','Arcade-DrMicro'],'quartus_preflow.log')
 inputs=identity()
 if stage!='map':
  prior=json.loads((R/'reports'/('quartus_'+('map' if stage=='fit' else 'fit')+'.json')).read_text())
  if prior['status']!='PASS' or prior['inputs']['sha256']!=inputs['sha256']:raise ValueError('Prior Quartus stage missing, failed or stale; rerun map/fit for current sources')
 result=dict(stage=stage,status='FAIL',version=version,inputs=inputs,device='5CSEBA6U23I7',started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 start=time.time()
 try:
  args=[executable(stage),'--read_settings_files=on','--write_settings_files=off','Arcade-DrMicro','-c','Arcade-DrMicro']
  if stage=='sta':args=[executable('sta'),'Arcade-DrMicro','-c','Arcade-DrMicro']
  log=run_stage(args,'quartus_'+stage+'.log')
  if stage=='sta':
   run_stage([executable('sta'),'-t','tools/quartus_corners.tcl'],'quartus_corners.log')
   rows=list(csv.DictReader((R/'reports/quartus_corners.csv').open()))
   if not rows or not {'setup','hold'}<=set(x['type'] for x in rows):raise ValueError('Incomplete timing corner audit')
   result['corners']=rows
   pulse_files=list((R/'reports').glob('quartus_corner_*_pulse.rpt'))
   pulse_slacks=[float(m[1]) for p in pulse_files for m in re.finditer(r'^;\s*(-?\d+\.\d+)\s*;',p.read_text(),re.M)]
   if not pulse_slacks or min(pulse_slacks)<0:raise ValueError('Missing or negative minimum pulse-width results')
   result['minimum_pulse_width_slack_ns']=min(pulse_slacks)
   result['scope']='Constrained paths at available operating conditions. External I/O coverage is incomplete; see quartus_unconstrained.rpt. No board-level timing sign-off.'
   result['timing_script_sha256']=hashlib.sha256((R/'tools/quartus_corners.tcl').read_bytes()).hexdigest()
   if any(float(x['slack_ns'])<0 for x in rows):raise ValueError('Negative timing slack; see quartus_corners.csv and detailed paths')
  if identity()['sha256']!=inputs['sha256']:raise ValueError('Quartus sources changed during the stage; result is stale')
  if stage=='sta' and 'timing requirements not met' in log.lower():raise ValueError('TimeQuest reports timing requirements not met; inspect timing report')
  result['status']='PASS'
  summary=R/'build/quartus'/('Arcade-DrMicro.'+stage+'.summary')
  if summary.exists():shutil.copy2(summary,R/'reports'/('quartus_'+stage+'.summary'))
 except Exception as e:result['reason']=str(e);raise
 finally:
  result['seconds']=round(time.time()-start,3)
  (R/'reports'/('quartus_'+stage+'.json')).write_text(json.dumps(result,indent=2))
 return result
if __name__=='__main__':main()
