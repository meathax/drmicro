"""Keep executable test results and strict equivalence gates separate."""
import json
from dev import R,build_identity

def main():
 tests=json.loads((R/'reports/test_report.json').read_text())
 required=['check_deps','check_roms','lint_core','test_unit','test_fixtures','check_platform','test_rotation','test_platform_video','test_platform_hps','check_project','build_sim','quartus_map','quartus_fit','quartus_sta']
 checks={k:tests.get(k,{'status':'NOT_RUN'})['status'] for k in required}
 comparisons={}
 for script in ['attract','play','dips','service','reset','two','cocktail']:
  p=R/'reports'/f'comparison_{script}.json'
  if not p.exists():comparisons[script]={'status':'NOT_RUN'};continue
  a=json.loads(p.read_text())
  comparisons[script]={k:a[k] for k in ['status','all_io_writes','sound_commands','io_reads']}
  comparisons[script].update(captures=len(a['frames']),exact_rgb_captures=sum(x['rgb_differing_pixels']==0 for x in a['frames']),max_rgb_differing_pixels=max(x['rgb_differing_pixels'] for x in a['frames']))
 outcomes={}
 for name in ['milestones','cold_boots','source_audit']:
  p=R/'reports'/f'{name}.json';outcomes[name]=json.loads(p.read_text()) if p.exists() else {'status':'NOT_RUN'}
 report={'status':'PASS' if all(v['status']=='PASS' for v in comparisons.values()) and all(v=='PASS' for v in checks.values()) and all(v['status']=='PASS' for v in outcomes.values()) else 'FAIL',
 'meaning':'Overall strict equivalence gate; passing subsystem/outcome checks do not override moving-game mismatches.',
 'subsystem_checks':checks,'outcomes':outcomes,'reference_comparisons':comparisons,'current_build':build_identity(),
 'hardware':{'status':'NOT_RUN','reason':'No RBF or DE10-Nano test. Quartus synthesis/fit/timing results are recorded separately under subsystem_checks.'},
 'remaining':{'implementation_comparison':'Water-animation state/pixel differences and death-transition I/O ordering remain unresolved; raw reset control bits differ only outside implemented bits 0/1.',
 'assets_tools':'None missing for current checks.',
 'hardware_facts':'Provisional raster/CPU phase, undocumented control bits and analogue/audio/reset behaviour need PCB evidence.',
 'future_build':'Resolve any Quartus timing findings and perform full physical MiSTer platform validation.'}}
 (R/'reports/verification_summary.json').write_text(json.dumps(report,indent=2))
 print('Wrote verification_summary.json; strict overall gate:',report['status'])
 return report
if __name__=='__main__':main()
