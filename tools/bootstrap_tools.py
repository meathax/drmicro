"""Optional portable Windows HDL tools. Project-local; no Quartus or PATH changes."""
import hashlib,json,pathlib,tarfile,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 req=urllib.request.Request('https://api.github.com/repos/YosysHQ/oss-cad-suite-build/releases/tags/2026-09-05',headers={'User-Agent':'drmicro'})
 info=json.load(urllib.request.urlopen(req))
 a=next(x for x in info['assets'] if 'windows-x64' in x['name'] and x['name'].endswith('.tgz'))
 d=R/'.tools';d.mkdir(exist_ok=True); p=d/a['name']
 print('Downloading portable HDL tools',a['name'],a['size'],flush=True)
 if not p.exists(): urllib.request.urlretrieve(a['browser_download_url'],p)
 (d/'tool-download.json').write_text(json.dumps({'url':a['browser_download_url'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2))
 with tarfile.open(p) as tf: tf.extractall(d,filter='data')
 print('Extracted',d,flush=True)
if __name__=='__main__':main()
