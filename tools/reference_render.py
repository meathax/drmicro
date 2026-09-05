"""Independent MAME-layout bit-address decoder and static renderer (checker only)."""
import json,pathlib,struct
from roms import R,manifest,load
def pixel(blob,bank,sprite,code,x,y):
 # MAME gfx_layout bit numbering is MSB first. First plane is highest pen bit.
 planes=([0,0x2000*8] if bank==0 else [0x4000*8,0x2000*8,0])
 xs=list(range(7,-1,-1))+(list(range(71,63,-1)) if sprite else [])
 ys=list(range(0,64,8))+(list(range(128,192,8)) if sprite else [])
 stride=256 if sprite else 64
 value=0
 for plane in planes:
  bit=plane+code*stride+xs[x]+ys[y]
  value=(value<<1)|((blob[bit//8]>>(7-bit%8))&1)
 return value
def render(payload,ram,flip=False):
 m=manifest();regions={r['name']:payload[r['offset']:r['offset']+r['length']] for r in m['regions']}
 out=[0]*(256*224)
 for bank in range(2):
  v=ram[0x2800 if bank==0 else 0x2000:0x3000 if bank==0 else 0x2800];gfx=regions['gfx'+str(bank+1)]
  for y in range(16,240):
   for x in range(256):
    xx,yy=(255-x,255-y) if flip else (x,y)
    tile=(yy//8)*32+xx//8;attr=v[tile+1024];code=v[tile]+((attr&192)<<2)
    pen=pixel(gfx,bank,False,code,xx%8^(7 if attr&16 else 0),yy%8^(7 if attr&32 else 0))
    if bank==0 or pen:out[(y-16)*256+x]=(256 if bank else 0)+(attr&15)*(8 if bank else 4)+pen
 for bank in range(2):
  v=ram[0x2800 if bank==0 else 0x2000:0x3000 if bank==0 else 0x2800];gfx=regions['gfx'+str(bank+1)]
  for o in range(0,32,4):
   yy,ch,attr,xx=v[o:o+4];code=(ch>>2)|(attr&192)
   fx=bool(ch&1)^flip;fy=bool(ch&2)^flip
   if flip:xx=(240-xx)&255
   else:yy=(240-yy)&255
   for y in range(16):
    dy=yy+y
    if not 16<=dy<240:continue
    for x in range(16):
     dx=(xx+x)&255
     pen=pixel(gfx,bank,True,code,15-x if fx else x,15-y if fy else y)
     if pen:out[(dy-16)*256+dx]=(256 if bank else 0)+(attr&15)*(8 if bank else 4)+pen
 return out
def rgb(payload,pens):
 r=next(r for r in manifest()['regions'] if r['name']=='proms');p=payload[r['offset']:]
 out=bytearray()
 for pen in pens:
  c=p[p[32+pen]&15]
  out.extend((sum(w*((c>>i)&1) for i,w in enumerate([33,71,151])),sum(w*((c>>(i+3))&1) for i,w in enumerate([33,71,151])),82*((c>>6)&1)+173*((c>>7)&1)))
 return bytes(out)
def ppm(path,pixels,width=256,height=224):path.write_bytes(f'P6\n{width} {height}\n255\n'.encode()+pixels)
def compare_snapshots(folder):
 payload,_=load();report=[]
 for f in sorted(pathlib.Path(folder).glob('*.ram')):
  flip=bool(json.loads(f.with_suffix('.json').read_text())['flip']);expected=render(payload,f.read_bytes(),flip)
  ppm(f.with_name(f.stem+'_static_reference.ppm'),rgb(payload,expected))
  actual=struct.unpack('<'+str(len(expected))+'H',f.with_suffix('.pen').read_bytes())
  diff=[i for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
  report.append(dict(frame=f.stem,differences=len(diff),first_xy=([diff[0]%256,diff[0]//256+16] if diff else None),note='Live frame versus end-of-frame snapshot; differences may be live VRAM timing'))
 (R/'reports/static_snapshot_comparison.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':compare_snapshots(R/'reports/captures/attract')
