"""Cross-platform driver; Quartus runs only through explicitly named stages."""
import argparse,concurrent.futures,hashlib,json,os,pathlib,shutil,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1]
os.chdir(R)
ENV=os.environ.copy()
SUITE=R/'.tools/oss-cad-suite'
if SUITE.exists():
 ENV['PATH']=os.pathsep.join([str(SUITE/'bin'),str(SUITE/'lib'),str(R/'.tools/w64devkit/bin'),ENV.get('PATH','')])
 ENV['VERILATOR_ROOT']=str(SUITE/'share/verilator')
def tool(name):
 candidates=[name+'.exe',name] if os.name=='nt' else [name]
 for c in candidates:
  p=shutil.which(c,path=ENV['PATH'])
  if p:return p
 raise FileNotFoundError('Missing tool: '+name)
def run(args,log=None):
 print('RUN', ' '.join(str(x) for x in args),flush=True)
 out=subprocess.run(list(map(str,args)),env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if log:(R/'reports'/log).write_text(out.stdout,encoding='utf-8')
 if out.returncode:print(out.stdout[-12000:]);raise RuntimeError('Command failed: '+str(out.returncode))
 print(out.stdout[-1500:],end='',flush=True)
 return out.stdout
def sources():return [x for x in (R/'sim/core.f').read_text().splitlines() if x and not x.startswith(('+','#'))]

def build_identity():
 files=[*sources(),'sim/core.f','sim/observe.vlt','sim/main.cpp']
 return dict(source_sha256=hashlib.sha256(b''.join((R/p).read_bytes() for p in sources())).hexdigest(),files={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in files},binary_sha256=hashlib.sha256((R/'build/drmicro_sim.exe').read_bytes()).hexdigest(),defines=['TV80_REFRESH'],nmi_line=239,nmi_x=316,frame_origin=240)
def fetch_dependencies():
 __import__('fetch_deps').main()
 __import__('setup_project').main()
 __import__('gen_spec').main()
 __import__('finalize_deps').main()
def lint_core():
 log=run([tool('verilator_bin' if os.name=='nt' else 'verilator'),'--lint-only','--top-module','drmicro_core','-Wall','--Wno-fatal','-f','sim/core.f'], 'lint_core.log')
 import re
 for line in log.splitlines():
  if re.match(r'%Warning-(LATCH|MULTIDRIVEN|UNOPTFLAT|WIDTHEXPAND|WIDTHTRUNC|IMPLICIT|UNDRIVEN|PINMISSING):',line):raise RuntimeError('Actionable core lint warning: '+line)
def check_deps():
 lock=json.loads((R/'third_party.lock.json').read_text());n=0
 for dep in lock.values():
  for group in ['files','materialized_files','patches']:
   for p,h in dep.get(group,{}).items():
    if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:raise ValueError('Dependency changed: '+p)
    n+=1
 print('PASS dependency hashes:',n)
def build_sim(jobs=2):
 run([tool('verilator_bin' if os.name=='nt' else 'verilator'),'--cc','--top-module','drmicro_core','sim/observe.vlt','--Mdir','build/fastobj','--Wno-fatal','-f','sim/core.f'],'build_sim_elaborate.log')
 include=pathlib.Path(ENV.get('VERILATOR_ROOT','/usr/share/verilator'))/'include'
 cpp=[R/'sim/main.cpp',*sorted((R/'build/fastobj').glob('*.cpp')),include/'verilated.cpp',include/'verilated_threads.cpp']
 objdir=R/'build/fastcpp';objdir.mkdir(exist_ok=True)
 flags=['-std=c++20','-O2','-pthread','-I'+str(include),'-I'+str(include/'vltstd'),'-Ibuild/fastobj']
 headers=max(p.stat().st_mtime for p in (R/'build/fastobj').glob('*.h'))
 def compile_one(p):
  obj=objdir/(p.stem+'.o')
  if not obj.exists() or obj.stat().st_mtime<max(p.stat().st_mtime,headers):
   out=subprocess.run([tool('g++'),*flags,'-c',str(p),'-o',str(obj)],env=ENV,capture_output=True,text=True)
   if out.returncode:raise RuntimeError(out.stdout+out.stderr)
   return str(obj),out.stdout+out.stderr
  return str(obj),'cached '+p.name+'\n'
 with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(jobs,8))) as pool:results=list(pool.map(compile_one,cpp))
 (R/'reports/build_sim_compile.log').write_text(''.join(log for _,log in results))
 run([tool('g++'),'-pthread',*[obj for obj,_ in results],'-o','build/drmicro_sim.exe'],'build_sim_link.log')
 (R/'build/drmicro_sim.build.json').write_text(json.dumps(build_identity(),indent=2))
def run_smoke(frames=120,script='attract'):
 __import__('roms').main(True)
 identity_path=R/'build/drmicro_sim.build.json'
 identity=build_identity()
 if identity_path.exists() and json.loads(identity_path.read_text())!=identity:raise ValueError('Simulation binary/source manifest differs; run build_sim first')
 run([R/'build/drmicro_sim.exe','build/drmicro.rom',str(frames),'reports/captures/'+script,script],'run_smoke_'+script+'.log')
 path=R/'reports/captures'/script/'result.json';result=json.loads(path.read_text())
 result.update(source_sha256=hashlib.sha256(b''.join((R/p).read_bytes() for p in sources())).hexdigest(),runner_sha256=hashlib.sha256((R/'sim/main.cpp').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256((R/'build/drmicro_sim.exe').read_bytes()).hexdigest(),payload_sha256=hashlib.sha256((R/'build/drmicro.rom').read_bytes()).hexdigest(),nmi_line=239,nmi_x=316,frame_origin=240,defines=['TV80_REFRESH'])
 result['build_identity']=identity
 path.write_text(json.dumps(result,indent=2))
def test_unit():
 for tb in ['units','cpu','cpu_timing','cpu_extended','cpu_refresh','cpu_nmi','memory']:
  run([tool('iverilog'),'-g2012','-s','tb_'+tb,'-o','build/tb_'+tb+'.vvp','-f','sim/core.f','tests/tb_'+tb+'.sv'],tb+'_compile.log')
  run([tool('vvp'),'build/tb_'+tb+'.vvp'],tb+'_run.log')
def test_fixtures():
 __import__('gen_fixtures').main()
 for tb in ['psg','adpcm','sound_integration','video']:
  run([tool('iverilog'),'-g2012','-s','tb_'+tb,'-o','build/tb_'+tb+'.vvp','-f','sim/core.f','tests/tb_'+tb+'.sv'],tb+'_compile.log')
  for flip in (range(2) if tb=='video' else range(1)):
   run([tool('vvp'),'build/tb_'+tb+'.vvp','+flip='+str(flip)],tb+'_run'+str(flip)+'.log')
def check_platform():
 log=run([tool('verilator_bin' if os.name=='nt' else 'verilator'),'--lint-only','--top-module','emu','-DMISTER_FB','-Wall','--Wno-fatal','-f','sim/platform.f'],'check_platform.log')
 __import__('lint_policy').check(log)
def test_rotation():
 run([tool('verilator_bin' if os.name=='nt' else 'verilator'),'--cc','--top-module','screen_rotate','--Mdir','build/rotation','--Wno-fatal','sys/arcade_video.v'],'rotation_elaborate.log')
 include=pathlib.Path(ENV.get('VERILATOR_ROOT','/usr/share/verilator'))/'include'
 run([tool('g++'),'-std=c++20','-O2','-pthread','-I'+str(include),'-I'+str(include/'vltstd'),'-Ibuild/rotation','sim/rotation.cpp',*sorted((R/'build/rotation').glob('*.cpp')),include/'verilated.cpp',include/'verilated_threads.cpp','-o','build/rotation_test.exe'],'rotation_compile.log')
 run([R/'build/rotation_test.exe'],'rotation_run.log')

def test_platform_video():
 run([tool('verilator_bin' if os.name=='nt' else 'verilator'),'--cc','--top-module','platform_video_top','--Mdir','build/platform_video','--Wno-fatal','-f','sim/platform.f','sim/platform_video_top.sv'],'platform_video_elaborate.log')
 include=pathlib.Path(ENV.get('VERILATOR_ROOT','/usr/share/verilator'))/'include'
 run([tool('g++'),'-std=c++20','-O2','-pthread','-I'+str(include),'-I'+str(include/'vltstd'),'-Ibuild/platform_video','sim/platform_video.cpp',*sorted((R/'build/platform_video').glob('*.cpp')),include/'verilated.cpp',include/'verilated_threads.cpp','-o','build/platform_video_test.exe'],'platform_video_compile.log')
 run([R/'build/platform_video_test.exe'],'platform_video_run.log')

def test_platform_hps():
 __import__('roms').main(True)
 run([tool('verilator_bin' if os.name=='nt' else 'verilator'),'--cc','--top-module','platform_hps_top','-DMISTER_FB','--Mdir','build/platform_hps','--Wno-fatal','-f','sim/platform.f','sim/platform_hps_top.sv'],'platform_hps_elaborate.log')
 include=pathlib.Path(ENV.get('VERILATOR_ROOT','/usr/share/verilator'))/'include'
 run([tool('g++'),'-std=c++20','-O2','-pthread','-I'+str(include),'-I'+str(include/'vltstd'),'-Ibuild/platform_hps','sim/platform_hps.cpp',*sorted((R/'build/platform_hps').glob('*.cpp')),include/'verilated.cpp',include/'verilated_threads.cpp','-o','build/platform_hps_test.exe'],'platform_hps_compile.log')
 run([R/'build/platform_hps_test.exe'],'platform_hps_run.log')
def record(name,fn):
 start=time.time();entry={'command':name,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'NOT_RUN'}
 try:
  result=fn()
  if isinstance(result,dict) and result.get('status')=='FAIL':raise RuntimeError('Comparison mismatch; see comparison report')
  entry['status']='PASS'
 except FileNotFoundError as e:entry.update(status='BLOCKED',reason=str(e))
 except Exception as e:entry.update(status='FAIL',reason=str(e))
 entry['seconds']=round(time.time()-start,3)
 entry['source_sha256']=hashlib.sha256(b''.join((R/p).read_bytes() for p in sources())).hexdigest()
 path=R/'reports/test_report.json';report=json.loads(path.read_text()) if path.exists() else {};report[name]=entry;path.write_text(json.dumps(report,indent=2))
 with (R/'reports/test_history.jsonl').open('a') as history:history.write(json.dumps(dict(entry,arguments=sys.argv[1:]))+'\n')
 print(entry['status'],name,entry.get('reason',''),flush=True)
 return entry['status']
def main():
 p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--frames',type=int,default=120);p.add_argument('--jobs',type=int,default=2);p.add_argument('--script',default='attract');a=p.parse_args()
 (R/'reports').mkdir(exist_ok=True);(R/'build').mkdir(exist_ok=True)
 commands={'fetch_deps':fetch_dependencies,'check_deps':check_deps,'check_roms':lambda:__import__('roms').main(),'pack_roms':lambda:__import__('roms').main(True),'lint_core':lint_core,'build_sim':lambda:build_sim(a.jobs),'run_smoke':lambda:run_smoke(a.frames,a.script),'test_unit':test_unit}
 commands['test_fixtures']=test_fixtures
 commands['run_reference']=lambda:__import__('run_reference').main(a.frames,a.script)
 commands['check_platform']=check_platform
 commands['check_project']=lambda:__import__('check_project').main()
 commands['test_rotation']=test_rotation
 commands['test_platform_video']=test_platform_video
 commands['test_platform_hps']=test_platform_hps
 commands['compare']=lambda:__import__('compare').main(a.script)
 commands['capture_assets']=lambda:__import__('capture_assets').main(a.script)
 commands['check_milestones']=lambda:__import__('check_milestones').main()
 commands['audit_source']=lambda:__import__('audit_source').main()
 commands['test_cold_boots']=lambda:__import__('test_cold_boots').main()
 commands['summarize_status']=lambda:__import__('summarize_status').main()
 for stage in ['map','fit','sta']:
  commands['quartus_'+stage]=lambda stage=stage:__import__('quartus').main(stage)
 if a.command=='test_all':
  order=['check_deps','check_roms','pack_roms','lint_core','test_unit','test_fixtures','check_platform','test_rotation','test_platform_video','test_platform_hps','check_project','build_sim','run_smoke','run_reference','compare','capture_assets']
  statuses=[record(k,commands[k]) for k in order]
  sys.exit(1 if 'FAIL' in statuses else 2 if 'BLOCKED' in statuses else 0)
 if a.command not in commands:raise ValueError('Command not implemented: '+a.command)
 status=record(a.command,commands[a.command]);sys.exit(0 if status=='PASS' else 2 if status=='BLOCKED' else 1)
if __name__=='__main__':main()
