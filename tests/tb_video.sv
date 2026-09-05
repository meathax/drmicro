`timescale 1ns/1ps
module tb_video;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,vreset=1,load_wr=0,cpu_wr=0;reg[16:0]la=0;reg[7:0]ld=0,cd=0;reg[15:0]ca=0;
 wire clearing;wire[7:0]cpu_data,vd,color;wire[11:0]va;wire[12:0]ga;wire[15:0]g0;wire[23:0]g1;wire[8:0]pen;wire[3:0]ind;
 wire[7:0]r,g,b,dy;wire[8:0]dx;wire hs,vs,hb,vb,pce,ev,deadline;
 reg ce=0;integer count=0,flip=0;reg[8:0]pp[0:2];
 always @(posedge clk)begin count<=count==9?0:count+1;ce<=count==9;pp[0]<=pen;pp[1]<=pp[0];pp[2]<=pp[1];end
 drmicro_memory mem(.clk(clk),.reset(reset),.load_wr(load_wr),.load_addr(la),.load_data(ld),.cpu_addr(ca),.cpu_wr(cpu_wr),.cpu_dout(cd),.cpu_din(cpu_data),.clearing(clearing),.video_addr(va),.video_data(vd),.gfx_addr(ga),.gfx0(g0),.gfx1(g1),.sample_addr(14'd0),.sample_data(),.pen_addr(pen),.indirect(ind),.color_addr({1'b0,ind}),.color_data(color));
 drmicro_video vid(.clk(clk),.reset(vreset),.ce(ce),.flip(flip[0]),.va(va),.vd(vd),.ga(ga),.g0(g0),.g1(g1),.pen(pen),.color(color),.red(r),.green(g),.blue(b),.hs(hs),.vs(vs),.hblank(hb),.vblank(vb),.pixel_ce(pce),.frame_event(ev),.debug_x(dx),.debug_y(dy),.deadline_error(deadline));
 reg[7:0]payload[0:drmicro_pkg::ROM_SIZE-1],ram[0:16383];reg[8:0]expected[0:57343];reg[23:0]rgb[0:57343];
 integer frames=0,checked=0,p=0;
 initial begin
  if($value$plusargs("flip=%d",flip))begin end
  $readmemh("build/fixtures/payload.hex",payload);$readmemh("build/fixtures/ram.hex",ram);
  if(flip==0)begin $readmemh("build/fixtures/pen0.hex",expected);$readmemh("build/fixtures/rgb0.hex",rgb);end
  else begin $readmemh("build/fixtures/pen1.hex",expected);$readmemh("build/fixtures/rgb1.hex",rgb);end
  repeat(5)@(negedge clk);reset=0;
  wait(!clearing);
  for(integer i=0;i<drmicro_pkg::ROM_SIZE;i=i+1)begin @(negedge clk);load_wr=1;la=i;ld=payload[i];end
  @(negedge clk);load_wr=0;
  for(integer i=0;i<16384;i=i+1)begin @(negedge clk);cpu_wr=1;ca=16'hc000+i;cd=ram[i];end
  @(negedge clk);cpu_wr=0;vreset=0;
  while(frames<2)begin
   @(posedge clk);#1;
   if(deadline)$fatal(1,"deadline missed");
   if(pce)begin
    if(dx==0&&dy==0)frames=frames+1;
    if(frames==1&&!hb&&!vb)begin
     p=(dy-16)*256+dx;
     if(pp[2]!==expected[p])$fatal(1,"pen flip=%0d xy=%0d,%0d actual=%h expected=%h",flip,dx,dy,pp[2],expected[p]);
     if({r,g,b}!==rgb[p])$fatal(1,"RGB xy=%0d,%0d actual=%h expected=%h",dx,dy,{r,g,b},rgb[p]);
     checked=checked+1;
    end
   end
  end
  if(checked!=57344)$fatal(1,"pixel count %0d",checked);
  $display("PASS independent renderer flip=%0d: %0d raw indices/RGB, no X, no deadline failures",flip,checked);$finish;
 end
endmodule
