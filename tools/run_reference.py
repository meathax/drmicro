import hashlib,json,os,pathlib,subprocess,xml.etree.ElementTree as E
from dev import R,ENV,run
def main(frames=120,script='attract'):
 exe=ENV.get('MAME') or str(R/'.tools/mame/mame.exe')
 if not pathlib.Path(exe).is_file():raise FileNotFoundError('MAME unavailable; set MAME or run optional tools/bootstrap_mame.py')
 out=R/'reports/captures'/('mame_'+os.getenv('DRMICRO_CAPTURE_NAME',script));out.mkdir(parents=True,exist_ok=True)
 (out/'completion.json').unlink(missing_ok=True)
 version=run([exe,'-version'],'mame_version.log')
 run([exe,'drmicro','-rompath','.','-verifyroms'],'mame_verifyroms.log')
 xml=run([exe,'drmicro','-listxml'],'mame_listxml.xml')
 from roms import manifest
 known={p['name']:p for r in manifest()['regions'] for p in r['parts']}
 for rom in E.fromstring(xml).findall("./machine[@name='drmicro']/rom"):
  p=known[rom.get('name')]
  assert (int(rom.get('size')),rom.get('crc'),rom.get('sha1'))==(p['length'],p['crc32'],p['sha1'])
 ENV['DRMICRO_REFERENCE_OUT']=out.relative_to(R).as_posix();ENV['DRMICRO_SCRIPT']=script;ENV['DRMICRO_FRAMES']=str(frames)
 args=[exe,'drmicro','-rompath','.','-nothrottle','-video','none','-sound','none','-skip_gameinfo','-noreadconfig','-cfg_directory','build/mame_cfg','-nvram_directory','build/mame_nvram','-snapshot_directory',str(out),'-noburnin','-norotate','-autoboot_delay','0','-autoboot_script','reference/capture.lua','-seconds_to_run',str((frames+59)//60+3)]
 if os.getenv('DRMICRO_DEBUG_TRACE'):
  (R/'build/debug_start.txt').write_text('g\n')
  args+=['-debug','-debugger','none','-debugscript','build/debug_start.txt']
 log=run(args,'run_reference_'+script+'.log')
 if 'error' in log.lower() or not (out/'completion.json').exists() or not (out/f'frame_{frames}.ram').exists():raise RuntimeError('MAME capture incomplete; inspect log')
 assert json.loads((out/'completion.json').read_text())==dict(frames=frames,script=script)
 result=dict(status='PASS',frames=frames,script=script,input_callback_offset=int(ENV.get('DRMICRO_REFERENCE_INPUT_OFFSET','0')),binary=version.strip(),source_spec_commit=manifest()['mame_commit'],binary_info=json.loads((R/'reports/mame_binary.json').read_text()),args=args)
 result['executable']={'path':str(pathlib.Path(exe).resolve()),'sha256':hashlib.sha256(pathlib.Path(exe).read_bytes()).hexdigest()}
 (out/'result.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
