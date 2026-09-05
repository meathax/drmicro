`timescale 1ns/1ps
module tb_adpcm;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;reg[3:0]din=0;wire signed[11:0]sound;wire sample,irq,vclk;
 jt5205 #(.INTERPOL(0),.VCLK_CEN(1)) dut(reset,clk,1'b1,2'd1,din,sound,sample,irq,vclk);
 reg[3:0]nibbles[0:255];reg[11:0]expected[0:255];integer n=0,ticks=0;
 // Independent controller stimulus and synchronous ROM, separate from decoder.
 reg start=0,request=0,creset=1;reg[7:0]command=0,romdata;
 wire[13:0]addr;wire[3:0]nibble;wire decreset;wire[14:0]position;
 reg[7:0]rom[0:16383];
 drmicro_adpcm_ctrl ctrl(clk,creset,start,request,command,addr,romdata,nibble,decreset,position);
 always @(posedge clk)romdata<=rom[addr];
 task wait_steps;begin repeat(5)@(negedge clk);end endtask
 task command_start(input [7:0] c);begin @(negedge clk);command=c;start=1;@(negedge clk);start=0;wait_steps();end endtask
 task req;begin @(negedge clk);request=1;@(negedge clk);request=0;wait_steps();end endtask
 initial begin
  for(integer i=0;i<16384;i=i+1)rom[i]=8'h70;
  rom[0]=8'hab;rom[1]=8'hcd;rom[256]=8'hef;rom[16383]=8'h12;
  wait_steps();creset=0;command_start(0);
  if(nibble!=10||position!=1||decreset)$fatal(1,"immediate start");
  req();if(nibble!=11||position!=2)$fatal(1,"low nibble");
  req();if(nibble!=12||position!=3)$fatal(1,"high nibble");
  command_start(1);if(nibble!=14||position!=513)$fatal(1,"restart address");
  req();if(nibble!=15||position!=514)$fatal(1,"restart low nibble");
  req();if(!decreset||position!=514)$fatal(1,"byte terminator");
  // A marker remains a whole-byte marker even at an odd nibble address.
  command_start(0);rom[0]=8'h70;req();if(!decreset||position!=1)$fatal(1,"odd marker");
  // Isolated fixture injection for the address-space wrap boundary.
  @(negedge clk);ctrl.position=15'h7ffe;req();if(nibble!=1||position!=32767)$fatal(1,"end high");
  req();if(nibble!=2||position!=0)$fatal(1,"15 bit wrap");
  // Restart before, coincident with, or after a pending timing request.
  for(integer phase=0;phase<6;phase=phase+1)begin
   @(negedge clk);request=1;
   @(negedge clk);request=0;
   repeat(phase)@(negedge clk);
   command_start(1);
   if(nibble!=14||position!=513||decreset)$fatal(1,"restart/request phase %0d",phase);
  end
  $display("PASS ADPCM sequencer high-first, immediate start, restart, both marker phases and wrap");
 end
 initial begin
  $readmemh("build/fixtures/adpcm_nibbles.hex",nibbles);$readmemh("build/fixtures/adpcm_expected.hex",expected);
  // Let reset converge to the donor's specified -2 rest level; timing continues.
  repeat(256)@(negedge clk);
  while(!vclk)@(negedge clk);
  reset=0;din=nibbles[0];
  while(n<256)begin
   @(posedge clk);
   if(sample)begin
    #1;if(sound!==expected[n])$fatal(1,"ADPCM pipeline n=%0d actual=%d expected=%d",n,sound,$signed(expected[n]));
    n=n+1;
    @(negedge clk);if(n<256)din=nibbles[n];
   end
  end
  $display("PASS JT5205 independent 256-nibble decoder vector, signed saturation and one-sample pipeline");$finish;
 end
endmodule
