"""Optional official MAME reference binary; no game ROM download."""
import hashlib,json,pathlib,subprocess,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 j=json.load(urllib.request.urlopen('https://api.github.com/repos/mamedev/mame/releases/tags/mame0289'))
 a=next(x for x in j['assets'] if x['name'].endswith('b_x64.exe'))
 p=R/'.tools'/a['name'];print('Downloading MAME reference',a['name'],flush=True)
 if not p.exists():urllib.request.urlretrieve(a['browser_download_url'],p)
 d=R/'.tools/mame';d.mkdir(exist_ok=True)
 subprocess.run([str(p),'-y','-o'+str(d)],stdout=subprocess.DEVNULL,check=True)
 tag=json.load(urllib.request.urlopen('https://api.github.com/repos/mamedev/mame/commits/'+j['tag_name']))['sha']
 (R/'reports/mame_binary.json').write_text(json.dumps(dict(tag=j['tag_name'],source_commit=tag,url=a['browser_download_url'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2))
 print('MAME extracted',flush=True)
if __name__=='__main__':main()
