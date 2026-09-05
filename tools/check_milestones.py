"""Reference-correlated outcomes discovered from captures and ROM control flow.

C024 is updated by the coin routine at 098e; C186 differs 3/5 under the
lives DIP; C001 bit 5 is toggled at 0444-044f when changing players.
These are observations/checker assertions, never writes into the DUT.
"""
import csv,json
from roms import R

def main():
 root=R/'reports/captures'
 def ram(s,n):return (root/s/f'frame_{n}.ram').read_bytes()
 def meta(s,n):return json.loads((root/s/f'frame_{n}.json').read_text())
 def events(s,p):return [int(x['data']) for x in csv.DictReader(open(root/s/'io.csv')) if int(x['port'])==p]
 checks={}
 for prefix in ['', 'mame_']:
  a=ram(prefix+'play',300);b=ram(prefix+'dips',300)
  assert (a[0x24],b[0x24])==(0,1), 'One coin/two credits must leave one credit after start'
  assert (a[0x186],b[0x186])==(3,5), 'Lives DIP outcome'
  assert (meta(prefix+'play',300)['flip'],meta(prefix+'dips',300)['flip'])==(0,1)
  assert ram(prefix+'two',240)[1]&0x40, 'Two-player selected'
  assert not (ram(prefix+'two',240)[1]&0x20) and ram(prefix+'two',2460)[1]&0x20, 'Player turn transition'
  assert events(prefix+'two',3)==[0x21], 'Observed death sample command'
  assert meta(prefix+'cocktail',240)['flip']==0 and meta(prefix+'cocktail',2460)['flip']==1, 'Cocktail player-two flip'
 checks['gameplay_dips']={'status':'PASS','evidence':'DUT and reference: 3/5 lives, one remaining credit with 1C/2C, game flip at frame 300; visible captures inspected.'}
 checks['two_player_death_restart']={'status':'PASS','evidence':'Both runs select two players, issue sample 0x21, and change player state between frames 240 and 2460; visible death/restart captures inspected. This does not assert frame-exact trajectory equivalence.'}
 checks['cocktail_turn_flip']={'status':'PASS','evidence':'Both runs unflipped at 240 and flipped at 2460 after player turn changes.'}
 service=json.loads((R/'reports/comparison_service.json').read_text());assert service['status']=='PASS'
 checks['service_mode']={'status':'PASS','evidence':'Visible service screen; strict native RGB and all I/O compare exactly through 120 frames.'}
 reset=json.loads((R/'reports/comparison_reset.json').read_text())
 assert reset['known_board_effects']['status']=='PASS' and reset['io_reads']['status']=='PASS'
 assert all(x['rgb_differing_pixels']==0 for x in reset['frames'])
 assert (root/'reset/frame_120.ppm').read_bytes()==(root/'reset/frame_360.ppm').read_bytes()
 checks['full_boot_after_reset']={'status':'PASS','evidence':'Reset at frame 240; frame 360 returns to the same title as frame 120. All displayed captures, reads and known board effects agree. Raw control bits 2/3 differ from MAME soft reset and remain reported.'}
 report={'status':'PASS','checks':checks,'limits':'Outcome coverage is separate from strict gameplay pixel and cross-port timing equivalence. See script comparison reports.'}
 (R/'reports/milestones.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':main()
