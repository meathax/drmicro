`timescale 1ns/1ps
module tb_rotation;
 reg clk=0;always #5 clk=~clk;
 reg ce=0,hs=0,vs=0,de=0,native_mode=0;reg[7:0]r=0,g=0,b=0;
 wire en,rot,dc,we,rd;wire[4:0]fmt;wire[11:0]width,height;wire[31:0]base;wire[13:0]stride;
 wire[7:0]burst,be;wire[28:0]addr;wire[63:0]data;
 screen_rotate dut(.CLK_VIDEO(clk),.CE_PIXEL(ce),.VGA_R(r),.VGA_G(g),.VGA_B(b),.VGA_HS(hs),.VGA_VS(vs),.VGA_DE(de),.rotate_ccw(1'b1),.no_rotate(native_mode),.flip(1'b0),.video_rotated(rot),.FB_EN(en),.FB_FORMAT(fmt),.FB_WIDTH(width),.FB_HEIGHT(height),.FB_BASE(base),.FB_STRIDE(stride),.FB_VBL(vs),.FB_LL(1'b1),.DDRAM_CLK(dc),.DDRAM_BUSY(1'b0),.DDRAM_BURSTCNT(burst),.DDRAM_ADDR(addr),.DDRAM_DIN(data),.DDRAM_BE(be),.DDRAM_WE(we),.DDRAM_RD(rd));
 integer frame=0,writes=0,offset=0,tx=0,ty=0,sx=0,sy=0,x,y;
 task pixel(input integer x,input integer y);begin
  @(negedge clk);de=x<8&&y<6;hs=x==10;vs=y==8;
  r=x+1;g=y+1;b=x+16*y;ce=1;
  @(negedge clk);ce=0;
  repeat(8)@(negedge clk);
 end endtask
 always @(posedge clk)if(we&&frame>=7&&!native_mode)begin
  if(width!=6||height!=8||stride!=32)$fatal(1,"rotation dimensions %0d %0d %0d",width,height,stride);
  if(be!==8'h0f&&be!==8'hf0)$fatal(1,"byte enables");
  offset=addr[19:0]*8+(be==8'hf0 ? 4:0);tx=(offset%stride)/4;ty=offset/stride;
  sx=data[7:0]-1;sy=data[15:8]-1;
  if(tx!=sy||ty!=7-sx)$fatal(1,"rotation label (%0d,%0d) became (%0d,%0d)",sx,sy,tx,ty);
  writes=writes+1;
 end
 initial begin
  for(frame=0;frame<9;frame=frame+1)for(y=0;y<10;y=y+1)for(x=0;x<12;x=x+1)pixel(x,y);
  if(writes!=96)$fatal(1,"rotation write count %0d",writes);
  native_mode=1;
  for(frame=0;frame<5;frame=frame+1)for(y=0;y<10;y=y+1)for(x=0;x<12;x=x+1)pixel(x,y);
  if(en||rot)$fatal(1,"native bypass");
  $display("PASS CCW labelled pixel mapping, byte lanes, stride, dimensions, native bypass (always-ready DDR sink)");$finish;
 end
endmodule
