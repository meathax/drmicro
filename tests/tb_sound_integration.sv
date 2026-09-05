`timescale 1ns/1ps
// Whole audio path: real divider, sequencer, synchronous sample ROM, JT5205
// decoder and three PSGs. Independent integer decoder checks every sample.
module tb_sound_integration;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,wr=0;reg[7:0]port_addr=0,data=0,rd;
 wire[13:0]addr;wire signed[15:0]audio;wire[14:0]p0,p1,p2,pos;wire signed[11:0]pcm;wire sample;
 // Accelerated enable schedule preserves the 8:1 chip clock ratio and gives
 // the synchronous ROM more than two clocks before every decoder edge.
 reg clock_reset=1;
 wire acen,pcen;
 drmicro_ce #(.CLOCK(5000),.RATE(384)) ac_real(clk,clock_reset,acen);
 drmicro_ce #(.CLOCK(5000),.RATE(3072)) pc_real(clk,clock_reset,pcen);
 drmicro_sound dut(clk,reset,pcen,acen,wr,port_addr,data,addr,rd,audio,p0,p1,p2,pcm,sample,pos);
 reg[7:0]rom[0:16383];always @(posedge clk)rd<=rom[addr];
 integer steps[0:48];integer index=0,current=-2,next_value=-2,diff,value,checks=0;
 real step_real;
 always @(posedge clk)begin
  if(reset||dut.pcm_reset)begin index=0;next_value=current;end
  if(sample)begin
   if(reset||dut.pcm_reset)begin
    current=(current>0||current< -2)?(current>>>1):-2;next_value=current;
   end else begin
    current=next_value;
    value=dut.nibble;
    diff=(steps[index]>>3)+((value&1)?(steps[index]>>2):0)+((value&2)?(steps[index]>>1):0)+((value&4)?steps[index]:0);
    next_value=current+((value&8)?-diff:diff);
    if(next_value>2047)next_value=2047;if(next_value< -2048)next_value=-2048;
    case(value&7)0,1,2,3:index=index-1;4:index=index+2;5:index=index+4;6:index=index+6;7:index=index+8;endcase
    if(index<0)index=0;if(index>48)index=48;
   end
   #1;
   if($signed(pcm)!==current)$fatal(1,"integrated ADPCM sample %0d: got %0d expected %0d",checks,$signed(pcm),current);
   if(^audio===1'bx)$fatal(1,"audio mixer X");
   checks=checks+1;
  end
 end
 task write_port(input[7:0]p,input[7:0]v);begin @(negedge clk);port_addr=p;data=v;wr=1;@(negedge clk);wr=0;end endtask
 initial begin
  step_real=16.0;for(integer i=0;i<49;i=i+1)begin steps[i]=$rtoi(step_real);step_real=step_real*1.1;end
  for(integer a=0;a<16384;a=a+1)begin rom[a]=8'((a*17+(a>>4))^8'hab);if(rom[a]==8'h70)rom[a]=8'h71;if((a&255)==24)rom[a]=8'h70;end
  repeat(5)@(negedge clk);clock_reset=0;
  repeat(20000)@(negedge clk);reset=0;
  for(integer p=0;p<3;p=p+1)begin write_port(8'(p),8'h9f);write_port(8'(p),8'hbf);write_port(8'(p),8'hdf);write_port(8'(p),8'hff);end
  for(integer command=0;command<64;command=command+1)begin
   // Each page contains 48 nibbles then a stop marker. Vary restart phase.
   repeat(command*3+1)@(negedge clk);write_port(3,8'(command));
   repeat(80)begin @(posedge sample);@(negedge clk);end
   if(!dut.pcm_reset||pos!=command*512+48)$fatal(1,"sample page/marker command %0d position %0d",command,pos);
  end
  if(checks<5120)$fatal(1,"incomplete audio coverage");
  $display("PASS integrated audio %0d samples: 64 sample pages, restarts, stop markers, digital decode and mixer without X",checks);$finish;
 end
endmodule
