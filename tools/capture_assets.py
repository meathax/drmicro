import array,json,pathlib,wave
from roms import R,load,manifest
from reference_render import pixel,ppm
def main(script='attract'):
 folder=R/'reports/captures'/script
 raw=folder/'audio.raw'
 if raw.exists():
  samples=array.array('h');samples.frombytes(raw.read_bytes())
  for i,name in enumerate(['sn1','sn2','sn3','msm5205','mix']):
   with wave.open(str(folder/(name+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(samples[i::5].tobytes())
 payload,_=load();out=R/'reports/captures/contact_sheets';out.mkdir(exist_ok=True)
 for bank in range(2):
  reg=next(r for r in manifest()['regions'] if r['name']=='gfx'+str(bank+1));blob=payload[reg['offset']:reg['offset']+reg['length']]
  for sprite in (False,True):
   side=16 if sprite else 8;count=256 if sprite else 1024;width=32*side;height=(count//32)*side;pixels=bytearray(width*height*3)
   for code in range(count):
    for y in range(side):
     for x in range(side):
      v=pixel(blob,bank,sprite,code,x,y)*255//(3 if bank==0 else 7);p=((code//32*side+y)*width+code%32*side+x)*3;pixels[p:p+3]=bytes([v]*3)
   ppm(out/f'bank{bank}_{"sprites" if sprite else "tiles"}.ppm',pixels,width,height)
 print('WAV stems/mix and independent tile/sprite contact sheets generated locally')
if __name__=='__main__':main()
