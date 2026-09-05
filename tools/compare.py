"""Compare captured RGB, raw indices against independent snapshots and I/O events."""
import csv,hashlib,json,pathlib,struct
from roms import R,load
from reference_render import render,rgb,ppm
def main(script='attract'):
 a=R/'reports/captures'/script;b=R/'reports/captures'/('mame_'+script)
 if not (a/'result.json').exists() or not(b/'result.json').exists():raise FileNotFoundError('DUT and MAME captures required')
 payload,_=load();report=dict(script=script,frames=[],functional_io={},notes=[])
 ar=json.loads((a/'result.json').read_text());br=json.loads((b/'result.json').read_text())
 if ar.get('frames')!=br.get('frames'):raise ValueError('DUT/reference frame limits differ; rerun the reference for the same frame count')
 limit=ar['frames'];wanted=sorted(set([n for n in [1,30,*range(60,limit+1,60),limit] if n<=limit]))
 from PIL import Image
 for number in wanted:
  f=b/f'frame_{number}.pixels'
  dut=a/(f.stem+'.ppm')
  if not dut.exists() or not f.exists():raise FileNotFoundError('Missing comparison frame '+f.stem)
  mame_raw=struct.unpack('<'+str(len(f.read_bytes())//4)+'I',f.read_bytes())
  backbuffer=bytes(v for p in mame_raw for v in [(p>>16)&255,(p>>8)&255,p&255])
  front=Image.open(b/(f.stem+'.png')).convert('RGB')
  if front.size!=(256,224):raise ValueError('Reference snapshot must be native 256x224')
  reference=front.tobytes()
  actual=Image.open(dut).convert('RGB').tobytes()
  differences=sum(actual[i:i+3]!=reference[i:i+3] for i in range(0,len(actual),3))
  ram=(b/(f.stem+'.ram')).read_bytes();flip=bool(json.loads((b/(f.stem+'.json')).read_text())['flip'])
  independent=render(payload,ram,flip);decoded=rgb(payload,independent)
  static_diff=sum(decoded[i:i+3]!=reference[i:i+3] for i in range(0,len(decoded),3))
  ppm(b/(f.stem+'_offline.ppm'),decoded)
  d_ram=(a/(f.stem+'.ram')).read_bytes();ramdiff=[i+0xc000 for i,(x,y) in enumerate(zip(ram,d_ram)) if x!=y]
  d_flip=bool(json.loads((a/(f.stem+'.json')).read_text())['flip'])
  d_pens=render(payload,d_ram,d_flip);d_static=rgb(payload,d_pens)
  dut_static_diff=sum(d_static[i:i+3]!=actual[i:i+3] for i in range(0,len(actual),3))
  observed_pens=struct.unpack('<57344H',(a/(f.stem+'.pen')).read_bytes())
  dut_pen_diff=sum(x!=y for x,y in zip(d_pens,observed_pens))
  im=Image.open(dut).transpose(Image.Transpose.ROTATE_90);im.resize((448,512),Image.Resampling.NEAREST).save(a/(f.stem+'.png'))
  positions=[i//3 for i in range(0,len(actual),3) if actual[i:i+3]!=reference[i:i+3]]
  sprite_equal=all(d_ram[o:o+32]==ram[o:o+32] for o in [0x2000,0x2800])
  report['frames'].append(dict(frame=f.stem,rgb_differing_pixels=differences,offline_mame_snapshot_differing_pixels=static_diff,backbuffer_vs_displayed_pixels=sum(backbuffer[i:i+3]!=reference[i:i+3] for i in range(0,len(reference),3)),sprite_records_equal=sprite_equal,video_ram_differing_addresses=[i for i in ramdiff if 0xe000<=i<0xf000],pixel_difference_bounds=([min(p%256 for p in positions),min(p//256+16 for p in positions),max(p%256 for p in positions),max(p//256+16 for p in positions)] if positions else None),ram_differing_addresses=ramdiff,dut_rgb_sha256=hashlib.sha256(actual).hexdigest(),reference_rgb_sha256=hashlib.sha256(reference).hexdigest()))
  report['frames'][-1].update(offline_dut_snapshot_differing_pixels=dut_static_diff,offline_dut_snapshot_differing_pens=dut_pen_diff)
 # Port 05 is explicitly noprw in the driver. Preserve raw traces, exclude
 # that no-op from functional command equivalence (its data varies with phase).
 def events(p):return [x for x in csv.DictReader(open(p)) if x['port']!='5']
 aa=events(a/'io.csv');bb=events(b/'io.csv')
 first=next((dict(index=i,dut=x,reference=y) for i,(x,y) in enumerate(zip(aa,bb)) if (x['port'],x['data'])!=(y['port'],y['data'])),None)
 report['functional_io']=dict(dut_count=len(aa),reference_count=len(bb),matched_common_prefix=first['index'] if first else min(len(aa),len(bb)),first_divergence=first)
 all_a=list(csv.DictReader(open(a/'io.csv')));all_b=list(csv.DictReader(open(b/'io.csv')))
 def signature(rows):return [(x['port'],x['data']) for x in rows]
 report['all_io_writes']={'status':'PASS' if signature(all_a)==signature(all_b) else 'FAIL','dut_count':len(all_a),'reference_count':len(all_b)}
 def effects(rows):return [(x['port'],int(x['data'])&3 if x['port']=='4' else int(x['data'])) for x in rows if x['port']!='5']
 report['known_board_effects']={'status':'PASS' if effects(all_a)==effects(all_b) else 'FAIL','scope':'Ordered writes to implemented ports; control bits 0/1 only, no-op port 05 excluded. Raw full-byte comparison remains strict.'}
 if (a/'reads.csv').exists() and (b/'reads.csv').exists():
  ra=list(csv.DictReader(open(a/'reads.csv')));rb=list(csv.DictReader(open(b/'reads.csv')))
  report['io_reads']={'status':'PASS' if signature(ra)==signature(rb) else 'FAIL','dut_count':len(ra),'reference_count':len(rb)}
 report['sound_commands']={}
 for port in range(4):
  da=[x['data'] for x in all_a if int(x['port'])==port];db=[x['data'] for x in all_b if int(x['port'])==port]
  report['sound_commands'][str(port)]=dict(status='PASS' if da==db else 'FAIL',dut_count=len(da),reference_count=len(db),first_divergence=next((i for i,(x,y) in enumerate(zip(da,db)) if x!=y),None))
 report['notes']=['Displayed native PNG is the reference: MAME screen:pixels() reads m_curbitmap, while snapshot uses m_curtexture; those differ after the frame buffer swap.','No-op port 05 is included in all_io_writes; historical functional_io retains its narrower scope.','Live scanline rendering and MAME instantaneous frame rendering are distinct timing models. All pixel differences remain visible.']
 report['reference_snapshot_self_check']={'status':'PASS' if all(x['offline_mame_snapshot_differing_pixels']==0 for x in report['frames']) else 'FAIL'}
 report['status']='PASS' if report['frames'] and report['reference_snapshot_self_check']['status']=='PASS' and report['all_io_writes']['status']=='PASS' and report.get('io_reads',{}).get('status','FAIL')=='PASS' and all(x['rgb_differing_pixels']==0 for x in report['frames']) else 'FAIL'
 (R/'reports'/('comparison_'+script+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='frames'},indent=2))
 return report
if __name__=='__main__':main()
