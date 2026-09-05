"""Optional project-local MinGW C++ compiler from the official w64devkit release."""
import hashlib,json,pathlib,subprocess,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 info=json.load(urllib.request.urlopen('https://api.github.com/repos/skeeto/w64devkit/releases/tags/v2.9.1'))
 a=next(x for x in info['assets'] if 'x64' in x['name'] and x['name'].endswith('.exe'))
 p=R/'.tools'/a['name'];print('Download',a['name'],a['size'],flush=True)
 if not p.exists():urllib.request.urlretrieve(a['browser_download_url'],p)
 (R/'.tools/cpp-download.json').write_text(json.dumps(dict(url=a['browser_download_url'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2))
 subprocess.run([str(p),'-y','-o'+str(R/'.tools')],check=True,stdout=subprocess.DEVNULL)
 print('Compiler extracted',flush=True)
if __name__=='__main__':main()
