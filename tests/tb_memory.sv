`timescale 1ns/1ps
module tb_memory;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,lw=0,cw=0;reg[16:0]la=0;reg[7:0]ld=0,cd=0;reg[15:0]ca=0;reg[11:0]va=0;
 wire[7:0]q,vq;wire clearing;
 drmicro_memory dut(.clk(clk),.reset(reset),.load_wr(lw),.load_addr(la),.load_data(ld),.cpu_addr(ca),.cpu_wr(cw),.cpu_dout(cd),.cpu_din(q),.clearing(clearing),.video_addr(va),.video_data(vq),.gfx_addr(13'd0),.gfx0(),.gfx1(),.sample_addr(14'd0),.sample_data(),.pen_addr(9'd0),.indirect(),.color_addr(5'd0),.color_data());
 task step;begin @(posedge clk);#1;end endtask
 initial begin
  repeat(3)step();@(negedge clk);reset=0;
  repeat(16383)step();if(!clearing)$fatal(1,"short clear");step();if(clearing)$fatal(1,"clear completion");
  // Sequential ROM programming is local fixture setup; integration separately
  // exercises the download pins, including completion/invalidation.
  for(integer i=0;i<49152;i=i+1)begin @(negedge clk);lw=1;la=i;ld=(i*29)^(i>>8);end
  @(negedge clk);lw=0;
  for(integer i=0;i<65536;i=i+1)begin
   @(negedge clk);ca=i;step();
   if(i<49152)begin if(q!==8'((i*29)^(i>>8)))$fatal(1,"ROM read at %h",i);end
   else if(q!==0)$fatal(1,"RAM not cleared %h",i);
  end
  @(negedge clk);ca=16'he000;va=0;cw=1;cd=8'h5a;step();
  if(q!==0||vq!==0)$fatal(1,"old-data collision");
  @(negedge clk);cw=0;step();if(q!==8'h5a||vq!==8'h5a)$fatal(1,"video bank1 dual port");
  @(negedge clk);ca=16'he800;va=12'h800;cw=1;cd=8'ha5;step();@(negedge clk);cw=0;step();
  if(q!==8'ha5||vq!==8'ha5)$fatal(1,"video bank0 dual port");
  // Clear wins and ROM survives a game reset.
  @(negedge clk);reset=1;step();@(negedge clk);reset=0;cw=1;ca=16'hc000;cd=255;
  repeat(16384)step();@(negedge clk);cw=0;step();if(q!==0)$fatal(1,"clear priority");
  @(negedge clk);ca=16'hbfff;step();if(q!==8'((49151*29)^(49151>>8)))$fatal(1,"reset destroyed ROM");
  $display("PASS all 65536 CPU addresses, sync latency, old-data collisions, VRAM bank order, clear priority/length, ROM preservation");$finish;
 end
endmodule
