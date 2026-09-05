`timescale 1ns/1ps
module tb_psg;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,wr=0;reg[7:0]data=0;wire[14:0]sound;wire[3:0]digital;wire[16:0]noise;
 reg[47:0]vectors[0:32767];
 sn76496_jt89 dut(clk,reset,1'b1,wr,data,sound,digital,noise);
 initial begin
  $readmemh("build/fixtures/psg.hex",vectors);
  repeat(4)@(negedge clk);reset=0;
  for(integer i=0;i<32768;i=i+1)begin
   wr=vectors[i][44];data=vectors[i][43:36];@(posedge clk);#1;
   if({digital,noise,sound}!==vectors[i][35:0])$fatal(1,"PSG cycle %0d actual %h expected %h",i,{digital,noise,sound},vectors[i][35:0]);
   @(negedge clk);
  end
  $display("PASS SN76496 all noise modes, tone-zero, rewrites, volumes, short write spacing, startup");$finish;
 end
endmodule
