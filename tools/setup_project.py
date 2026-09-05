"""Materialize pinned donors and reproducible, attributed adaptations."""
import difflib,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 for source,dest in [('reference/template/sys','sys'),('reference/bankpanic/rtl/tv80','rtl/vendor/tv80')]:
  shutil.copytree(R/source,R/dest,dirs_exist_ok=True)
 for file in ['pll.v','pll.qip']:
  shutil.copy2(R/'reference/template/rtl'/file,R/'rtl'/file)
 shutil.copytree(R/'reference/template/rtl/pll',R/'rtl/pll',dirs_exist_ok=True)
 # Standard SystemVerilog scoping fixes, retained as patches against the pin.
 (R/'patches').mkdir(exist_ok=True)
 for file in ['hps_io.sv','hq2x.sv','video_mixer.sv','arcade_video.v','scandoubler.v','sys_top.v']:
  path=R/'sys'/file;old=path.read_text();new=old
  if file=='hps_io.sv':
   declarations=[]
   for line in old.splitlines(True):
    if line.strip().startswith(('reg ','wire ')) and any((' '+n+';') in line for n in ['kbd_data','kbd_we','kbd_rd','kbd_data_host','mouse_data','mouse_we','mouse_rd','mouse_data_host']):
     declarations.append(line.strip());new=new.replace(line,'')
   new=new.replace('wire [15:0] vc_dout;', '\n'.join(declarations)+'\nwire [15:0] vc_dout;')
   new=new.replace('wire [15:0] vc_dout;', "generate if(!PS2DIV) begin\n assign kbd_data_host=9'd0;\n assign mouse_data_host=9'd0;\nend endgenerate\nwire [15:0] vc_dout;")
  elif file=='hq2x.sv':new=new.replace('output [23:0] Result','output reg [23:0] Result')
  elif file=='video_mixer.sv':
   # Generate branches do not export their local wires to the gamma instance.
   new=new.replace('generate\n\tif(GAMMA && HALF_DEPTH)', 'wire [DWIDTH_SD:0] R_in, G_in, B_in;\ngenerate\n\tif(GAMMA && HALF_DEPTH)',1)
   for color in ['R','G','B']:
    new=new.replace(f'wire [7:0] {color}_in ',f'assign {color}_in ')
    new=new.replace(f'wire [DWIDTH:0] {color}_in ',f'assign {color}_in ')
  elif file=='arcade_video.v':
   new=new.replace('.scandoubler(scandoubler),', ".HDMI_FREEZE(1'b0),\n\t.freeze_sync(),\n\t.scandoubler(scandoubler),",1)
  elif file=='scandoubler.v':
   new=new.replace('\t.clk(clk_vid),', "\t.mono(1'b0),\n\t.clk(clk_vid),",1)
  elif file=='sys_top.v':
   # Cyclone V clock select inputs 2/3 require PLL outputs. Input 1 also
   # accepts a clock pin, permitting this core's direct 50 MHz video clock.
   for select in ['~vga_fb & direct_video','~vga_fb & ~vga_scaler']:
    new=new.replace(".clkselect({1'b1, "+select+"})", ".clkselect({~("+select+"), "+select+"})")
   new=new.replace(".inclk({clk_vid, hdmi_clk_out, 2'b00})", ".inclk({1'b0, hdmi_clk_out, clk_vid, 1'b0})")
  path.write_text(new)
  (R/'patches'/(file+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/sys/'+file,tofile='b/sys/'+file)))
 old=(R/'rtl/vendor/jt5205/hdl/jt5205_adpcm.v').read_text()
 new=old.replace("sound>12'd0 || sound < -12'd2", "sound>12'sd0 || sound < -12'sd2")
 (R/'rtl/derived').mkdir(exist_ok=True)
 (R/'rtl/derived/jt5205_adpcm.v').write_text(new)
 (R/'patches/jt5205_adpcm.v.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/rtl/vendor/jt5205/hdl/jt5205_adpcm.v',tofile='b/rtl/derived/jt5205_adpcm.v')))
 old=(R/'rtl/vendor/tv80/tv80_mcode.v').read_text()
 start=old.index('// RET\n');end=old.index('// case: 8\'b11001001',start)
 block=old[start:end].replace("TStates = 3'b101;", "// Zilog UM0080: unconditional Z80 RET is 4+3+3, not 5+3+3.\n                        TStates = (Mode == 0) ? 3'b100 : 3'b101;")
 new=old[:start]+block+old[end:]
 start=new.index('// NMI\n');end=new.index('// INT (IM 2)',start)
 block=new[start:end].replace("TStates = 3'b100;", "TStates = (Mode == 0) ? 3'b011 : 3'b100;")
 new=new[:start]+block+new[end:]
 (R/'rtl/derived/tv80_mcode.v').write_text(new)
 (R/'patches/tv80_mcode.v.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/rtl/vendor/tv80/tv80_mcode.v',tofile='b/rtl/derived/tv80_mcode.v')))
 old=(R/'rtl/vendor/tv80/tv80_core.v').read_text()
 start=old.index('ACC <= R;');end=old.index("2'b10 :",start)
 block=old[start:end].replace('(I == 0)','(R == 0)').replace('<= I[7]','<= R[7]')
 block=block.replace('F[Flag_H] <= 0;', 'F[Flag_X] <= R[3];\n                            F[Flag_Y] <= R[5];\n                            F[Flag_H] <= 0;')
 new=old[:start]+block+old[end:]
 # NMI's five-state M1 already includes its extra internal cycle; the two
 # maskable-interrupt acknowledge waits do not apply to an NMI.
 start=new.index('Auto_Wait = 1\'b0;')
 new=new[:start]+new[start:].replace("IntCycle == 1'b1 || NMICycle == 1'b1", "IntCycle == 1'b1 || (NMICycle == 1'b1 && Mode != 0)",1)
 (R/'rtl/derived/tv80_core.v').write_text(new)
 (R/'patches/tv80_core.v.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/rtl/vendor/tv80/tv80_core.v',tofile='b/rtl/derived/tv80_core.v')))
 qsf=(R/'reference/template/Template.qsf').read_text().replace('#set_global_assignment -name VERILOG_MACRO "MISTER_FB=1"','set_global_assignment -name VERILOG_MACRO "MISTER_FB=1"')
 qsf=qsf.replace('PROJECT_OUTPUT_DIRECTORY output_files','PROJECT_OUTPUT_DIRECTORY build/quartus').replace('NUM_PARALLEL_PROCESSORS ALL','NUM_PARALLEL_PROCESSORS 2')
 (R/'Arcade-DrMicro.qsf').write_text(qsf)
 (R/'Arcade-DrMicro.qpf').write_text('QUARTUS_VERSION = "17.0"\nPROJECT_REVISION = "Arcade-DrMicro"\n')
 (R/'Arcade-DrMicro.sdc').write_text('# Game uses platform-defined CLK_50M. No additional false paths.\n# Upstream sys_top.sdc defines the input clocks. No Quartus validation.\n')
 srcs=(R/'sim/core.f').read_text().splitlines()
 defines=[p[len('+define+'):] for p in srcs if p.startswith('+define+')]
 srcs=[p for p in srcs if p and not p.startswith(('+','#'))]
 (R/'files.qip').write_text('\n'.join('set_global_assignment -name VERILOG_MACRO '+d for d in defines)+'\n'+'\n'.join(f'set_global_assignment -name {"SYSTEMVERILOG_FILE" if p.endswith(".sv") else "VERILOG_FILE"} {p}' for p in srcs+['Arcade-DrMicro.sv'])+'\nset_global_assignment -name SDC_FILE Arcade-DrMicro.sdc\n')
if __name__=='__main__':main()
