import json,random,struct
from roms import R,manifest
from reference_render import render,rgb
def hexfile(path,data,width=2):path.write_text(''.join(f'{v:0{width}x}\n' for v in data))
def main():
 d=R/'build/fixtures';d.mkdir(parents=True,exist_ok=True);rnd=random.Random(1983)
 payload=bytes(rnd.randrange(256) for _ in range(manifest()['length']))
 ram=bytearray(rnd.randrange(256) for _ in range(16384))
 # Adversarial coincident sprites, flips, horizontal wrap; asymmetric planes.
 for b in (0x2000,0x2800):
  for n in range(8):ram[b+4*n:b+4*n+4]=bytes([112,n*29,(n*37)&255,(248+n*3)&255])
 hexfile(d/'payload.hex',payload);hexfile(d/'ram.hex',ram)
 for flip in (0,1):
  p=render(payload,ram,bool(flip));hexfile(d/f'pen{flip}.hex',p,3)
  colors=rgb(payload,p);hexfile(d/f'rgb{flip}.hex',[int.from_bytes(colors[i:i+3],'big') for i in range(0,len(colors),3)],6)
 # Independent SN76496 discrete event model, observed every system clock.
 tone=[0]*3;volume=[0]*4;count=[0]*4;state=65536;out=[0]*4;reg=0;mode=0;np=0
 div=0;vectors=[];n=32768
 schedule={0:0x9f,1:0xbf,2:0xdf,3:0xff,32:0x80,33:0,64:0x90,96:0xa1,97:0,128:0xb0,160:0xc2,161:0,192:0xd0}
 for i in range(16):schedule[256+i*41]=0x90|i
 for mode0 in range(8):schedule[1100+mode0*2000]=0xe0|mode0;schedule[1101+mode0*2000]=0xf0;schedule[1300+mode0*2000]=mode0
 for i in range(18000,n,47):schedule[i]=rnd.randrange(256)
 voltab=[int(8191/(1.258925412**i)) for i in range(15)]+[0]
 for cycle in range(n):
  if div==15:
   for c in range(4):
    count[c]-=1
    if count[c]<=0:
     if c<3:out[c]^=1;count[c]=tone[c] or 1024
     else:state=(state>>1)|(((bool(state&4)^bool((state&8)and(mode&4))))<<16);out[3]=state&1;count[3]=np
  div=(div+1)%16
  data=schedule.get(cycle,0);write=cycle in schedule
  if write:
   if data&128:reg=(data>>4)&7
   c=reg//2
   if reg in (0,2,4):
    tone[c]=((tone[c]&0x3f0)|(data&15)) if data&128 else ((tone[c]&15)|((data&63)<<4))
    if reg==4 and mode&3==3:np=(tone[2]or 1024)*2
   elif reg==6:mode=data&7;np=(tone[2]or 1024)*2 if mode&3==3 else 1<<(5+(mode&3));state=65536
   else:volume[c]=data&15
  dig=sum(v<<i for i,v in enumerate(out));snd=sum(voltab[v] for o,v in zip(out,volume) if o)
  vectors.append((int(write)<<44)|(data<<36)|(dig<<32)|(state<<15)|snd)
 hexfile(d/'psg.hex',vectors,12)
 # MSM5205 independent integer step algorithm. JT output lags by one sample
 # and starts at -2, unlike MAME's zero-reset baseline.
 steps=[int(16*(1.1**i)) for i in range(49)];index=0;signal=-2;expected=[]
 nibs=[7]*70+[15]*70+[rnd.randrange(16) for _ in range(116)]
 for nib in nibs:
  expected.append(signal&4095);step=steps[index]
  diff=(step>>3)+((step>>2) if nib&1 else 0)+((step>>1) if nib&2 else 0)+(step if nib&4 else 0)
  signal=max(-2048,min(2047,signal+(-diff if nib&8 else diff)))
  index=max(0,min(48,index+[-1,-1,-1,-1,2,4,6,8][nib&7]))
 hexfile(d/'adpcm_nibbles.hex',nibs,1);hexfile(d/'adpcm_expected.hex',expected,3)
 print('Generated independent renderer and',n,'PSG vectors')
if __name__=='__main__':main()
