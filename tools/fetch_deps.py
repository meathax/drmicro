"""Fetch immutable source archives; never fetch game ROMs."""
import hashlib, io, json, pathlib, tarfile, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOS = {
 'mame': ('mamedev/mame', 'reference/mame', ['src/mame/sanritsu/drmicro.cpp','src/devices/sound/sn76496.cpp','src/devices/sound/sn76496.h','src/devices/sound/msm5205.cpp','src/devices/sound/msm5205.h','COPYING']),
 'template': ('MiSTer-devel/Template_MiSTer', 'reference/template', None),
 'tv80': ('MiSTer-devel/Arcade-BankPanic_MiSTer','reference/bankpanic', None),
 'jt89': ('jotego/jt89','rtl/vendor/jt89', None),
 'jt5205': ('jotego/jt5205','rtl/vendor/jt5205', None),
}
def get(url):
 return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'DrMicro-source-build'}),timeout=120).read()
def main():
 lockpath=ROOT/'third_party.lock.json'
 lock=json.loads(lockpath.read_text()) if lockpath.exists() else {}
 for name,(repo,dest,selected) in REPOS.items():
  if name in lock and all((ROOT/p).exists() for p in lock[name].get('files',{})):
   print('present',name,flush=True); continue
  commit=lock.get(name,{}).get('commit') or json.loads(get(f'https://api.github.com/repos/{repo}/commits/HEAD'))['sha']
  files={}
  if selected:
   selected=sorted(set(selected+[str(pathlib.PurePosixPath(p).relative_to(dest)) for p in lock.get(name,{}).get('files',{}) if p.startswith(dest+'/')]))
   entries=[(p,get(f'https://raw.githubusercontent.com/{repo}/{commit}/{p}')) for p in selected]
  else:
   data=get(f'https://codeload.github.com/{repo}/tar.gz/{commit}')
   with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
    entries=[('/'.join(m.name.split('/')[1:]),tf.extractfile(m).read()) for m in tf.getmembers() if m.isfile()]
  for rel,data in entries:
   if '..' in pathlib.PurePosixPath(rel).parts: raise ValueError(rel)
   if data.lstrip().lower().startswith(b'<!doctype html'): raise ValueError('HTML response '+rel)
   path=ROOT/dest/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
   files[path.relative_to(ROOT).as_posix()]=hashlib.sha256(data).hexdigest()
  lock.setdefault(name,{})
  lock[name].update({'url':f'https://github.com/{repo}','commit':commit,'destination':dest,'files':files})
  lockpath.write_text(json.dumps(lock,indent=2)+'\n')
  print('pinned',name,commit,len(files),flush=True)
if __name__=='__main__':
 main()
 import setup_project
 setup_project.main()
