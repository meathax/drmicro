import hashlib,json,pathlib,zipfile,zlib
R=pathlib.Path(__file__).resolve().parents[1]
def manifest():return json.loads((R/'reference/rom_manifest.json').read_text())
def load(path=None):
 m=manifest();found={}
 candidates=[pathlib.Path(path)] if path else list(R.glob('drmicro.zip'))+list(R.glob('roms/**/drmicro.zip'))+list(R.glob('game/**/drmicro.zip'))+list(R.glob('games/**/drmicro.zip'))
 for c in candidates:
  with zipfile.ZipFile(c) as z:
   for n in z.namelist():
    if not n.endswith('/'):found[pathlib.PurePosixPath(n).name]=z.read(n)
 for d in ['roms','game','games']:
  for p in (R/d).rglob('*'):
   if p.is_file() and p.suffix!='.zip':found.setdefault(p.name,p.read_bytes())
 payload=bytearray();audit=[]
 for reg in m['regions']:
  for p in reg['parts']:
   b=found.get(p['name'])
   if b is None:raise FileNotFoundError(p['name'])
   crc=f'{zlib.crc32(b):08x}';sha=hashlib.sha1(b).hexdigest()
   if (len(b),crc,sha)!=(p['length'],p['crc32'],p['sha1']):raise ValueError('ROM mismatch '+p['name'])
   payload+=b;audit.append(dict(name=p['name'],length=len(b),crc32=crc,sha1=sha))
 return bytes(payload),audit
def main(pack=False):
 b,a=load();(R/'reports').mkdir(exist_ok=True)
 (R/'reports/rom_audit.json').write_text(json.dumps(dict(status='PASS',parts=a,payload_sha256=hashlib.sha256(b).hexdigest()),indent=2))
 if pack:
  (R/'build').mkdir(exist_ok=True);(R/'build/drmicro.rom').write_bytes(b)
 print('PASS:',len(a),'ROMs,',len(b),'bytes, SHA256',hashlib.sha256(b).hexdigest())
if __name__=='__main__':main(True)
