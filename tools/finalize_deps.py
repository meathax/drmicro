"""Record materialized dependency closure, per-file licenses and adaptations."""
import hashlib,json,pathlib,shutil,urllib.request
from roms import R
def main():
 p=R/'third_party.lock.json';lock=json.loads(p.read_text())
 configs={
 'mame':dict(license='BSD-3-Clause for the selected driver/sound files; COPYING describes the larger project',used_modules=[],configuration='Behavioural oracle only; never linked into DUT'),
 'template':dict(license='GPL-2.0-or-later per file headers; retain vendor IP notices individually',used_modules=['hps_io','video_calc','arcade_video','screen_rotate','video_mixer','scandoubler','Hq2x','gamma_corr','sync_fix'],configuration='MISTER_FB=1; WIDE=0; PS2DIV=0; physical sys_top/PLL/DDR not simulated'),
 'tv80':dict(license='MIT-style permission notice, Guy Hutchison 2004; derived from T80 by Daniel Wallner',used_modules=['tv80s','tv80_core','tv80_alu','tv80_reg','tv80_mcode'],configuration='Mode=0,T2Write=0,IOWait=1,TV80_REFRESH=1; Mode 0 RET/NMI timing and LD A,R flags corrected in attributed derived sources; wait/int/busrq inactive high'),
 'jt89':dict(license='GPL-3.0-or-later, Jose Tejada Gomez; individual upstream notices retained',used_modules=['sn76496_jt89 (attributed adaptation)'],configuration='INTERPOL16=0 inspected; variant-dependent donor oscillator/mixer replaced per MAME SN76496'),
 'jt5205':dict(license='GPL-3.0-or-later, Jose Tejada Gomez',used_modules=['jt5205','jt5205_timing','jt5205_adpcm (signed-reset comparison patch)'],configuration='INTERPOL=0,VCLK_CEN=1,sel=1'),
 }
 for k,v in configs.items():lock[k].update(v)
 supplemental=['docs/legal/BSD-3-Clause','src/emu/drawgfx.cpp']
 for rel in supplemental:
  target=R/'reference/mame'/rel
  if not target.exists():
   b=urllib.request.urlopen(f"https://raw.githubusercontent.com/mamedev/mame/{lock['mame']['commit']}/{rel}").read();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
  lock['mame']['files'][target.relative_to(R).as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
 for key,paths in [('template',[*(R/'sys').rglob('*'),*(R/'rtl/pll').rglob('*'),R/'rtl/pll.v',R/'rtl/pll.qip']),('tv80',[*list((R/'rtl/vendor/tv80').glob('*')),R/'rtl/derived/tv80_mcode.v',R/'rtl/derived/tv80_core.v']),('jt89',[R/'rtl/sn76496_jt89.sv']),('jt5205',[R/'rtl/derived/jt5205_adpcm.v'])]:
  lock[key]['materialized_files']={x.relative_to(R).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in paths if x.is_file()}
 for key,patches in [('template',['hps_io.sv.patch','hq2x.sv.patch','video_mixer.sv.patch','arcade_video.v.patch','scandoubler.v.patch','sys_top.v.patch']),('tv80',['tv80_mcode.v.patch','tv80_core.v.patch']),('jt5205',['jt5205_adpcm.v.patch'])]:
  lock[key]['patches']={('patches/'+x):hashlib.sha256((R/'patches'/x).read_bytes()).hexdigest() for x in patches}
 # Capture each retained HDL/include header's own license statement. A broad
 # project label never overrides a file's upstream notice.
 for dep in lock.values():
  dep['license_headers']={}
  for filename in dep['files']:
   f=R/filename
   if f.suffix in ['.v','.sv','.vhd','.vh','.cpp','.h']:
    lines=f.read_text(errors='replace').splitlines()[:50]
    dep['license_headers'][filename]=[l for l in lines if any(w in l.lower() for w in ['copyright','license','permission is hereby','author:'])]
 p.write_text(json.dumps(lock,indent=2)+'\n')
 shutil.copy2(R/'rtl/vendor/jt89/LICENSE',R/'LICENSE')
 # Preserve immutable URLs and checksums for the optional tool binaries used.
 tool_info={}
 for f in ['tool-download.json','cpp-download.json']:
  if (R/'.tools'/f).exists():tool_info[f]=json.loads((R/'.tools'/f).read_text())
 if (R/'reports/mame_binary.json').exists():tool_info['mame']=json.loads((R/'reports/mame_binary.json').read_text())
 (R/'reports/tool_provenance.json').write_text(json.dumps(tool_info,indent=2))
 print('Dependency configurations, materialized hashes, patch hashes and file license headers recorded')
if __name__=='__main__':main()
