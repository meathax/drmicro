"""Check the distributable Git path set for user ROMs and generated binaries."""
import hashlib,json,pathlib,shutil,subprocess
from roms import R,load

def main():
 git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
 paths=subprocess.check_output([git,'ls-files','--cached','--others','--exclude-standard','-z'],cwd=R).decode().split('\0')
 paths=sorted(set(p for p in paths if p and (R/p).is_file()))
 payload,parts=load();forbidden={hashlib.sha256(payload).hexdigest()};offset=0
 for part in parts:
  forbidden.add(hashlib.sha256(payload[offset:offset+part['length']]).hexdigest());offset+=part['length']
 problems=[]
 for p in paths:
  if p.startswith(('build/','.tools/','reports/captures/','roms/','game/','games/')) or pathlib.Path(p).suffix.lower() in ['.rbf','.sof','.exe','.vvp','.wav','.rom','.zip']:
   problems.append(p+': generated/private asset path')
  elif hashlib.sha256((R/p).read_bytes()).hexdigest() in forbidden:problems.append(p+': matches user ROM/payload')
 result={'status':'FAIL' if problems else 'PASS','files_checked':len(paths),'problems':problems,'scope':'Git eligible source paths; original ROM member and packed-payload SHA256 matches plus generated-asset path/extension checks. Pinned donor test data and schematic remain attributed upstream assets.'}
 (R/'reports/source_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 if problems:raise ValueError('Source asset audit failed')
 return result
if __name__=='__main__':main()
