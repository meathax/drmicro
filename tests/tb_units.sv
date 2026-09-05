`timescale 1ns/1ps
module tb_units;
 reg clk=0;always #10 clk=~clk;
 reg reset=1,dl=0,wr=0;reg[15:0] idx=0;reg[26:0] addr=0;reg[7:0] data=0;
 wire valid,error,loading,mw;wire[16:0] ma;wire[7:0] md;
 integer writes=0;
 drmicro_rom_loader #(.SIZE(16)) loader(clk,reset,dl,wr,idx,addr,data,valid,error,loading,mw,ma,md);
 always @(posedge clk)if(mw)writes<=writes+1;
 task step;begin @(posedge clk);#1;end endtask
 task put(input integer a);begin @(negedge clk);addr=a;wr=1;step();@(negedge clk);wr=0;step();end endtask
 task begin_load;begin @(negedge clk);dl=1;idx=0;step();end endtask
 task end_load;begin @(negedge clk);dl=0;step();step();end endtask
 wire ce;drmicro_ce #(.RATE(3),.CLOCK(10)) rate(clk,reset,ce);
 integer pulses=0;
 reg[31:0] j0=0,j1=0;reg[10:0]key=0;wire[7:0]p1,p2;
 drmicro_inputs inp(clk,reset,j0,j1,key,p1,p2);
 reg mr=1,ior=1,rd=1,ww=1,rf=1,m1=1;
 reg[15:0]ba=0;wire[7:0]bd;wire bmw,biw;
 drmicro_bus bus(clk,reset,mr,ior,rd,ww,rf,m1,ba,8'h5a,8'h12,8'h34,8'h4d,8'h00,bd,bmw,biw);
 initial begin
  repeat(3)step();@(negedge clk);reset=0;
  repeat(100)begin step();if(ce)pulses=pulses+1;end
  if(pulses!=30)$fatal(1,"rational CE count");
  begin_load();for(integer i=0;i<16;i=i+1)put(i);end_load();
  if(!valid||error||writes!=16)$fatal(1,"complete loader/final byte");
  @(negedge clk);idx=254;dl=1;step();put(0);end_load();
  if(!valid||writes!=16)$fatal(1,"DIP download invalidates ROM");
  begin_load();put(0);put(1);end_load();if(valid||!error)$fatal(1,"short download");
  begin_load();put(0);put(2);end_load();if(valid||!error)$fatal(1,"out of order");
  begin_load();for(integer i=0;i<16;i=i+1)put(i);put(16);end_load();if(valid||!error)$fatal(1,"overflow");
  begin_load();for(integer i=0;i<16;i=i+1)put(i);end_load();if(!valid||error)$fatal(1,"redownload recovery");
  begin_load();put(0);@(negedge clk);idx=7;step();end_load();if(valid||!error)$fatal(1,"mid-session index change");
  // Start and first byte on the same edge, including recovery from error.
  @(negedge clk);idx=0;dl=1;addr=0;wr=1;step();
  repeat(4)step();if(loader.count!=1)$fatal(1,"stretched write captured repeatedly");
  @(negedge clk);wr=0;step();for(integer i=1;i<16;i=i+1)put(i);end_load();
  if(!valid||error)$fatal(1,"same-edge start recovery");
  j0=(1<<3)|(1<<0)|(1<<4)|(1<<7);#1;if(p1!=8'h31)$fatal(1,"fourway vertical priority");
  j0=(1<<3)|(1<<2);#1;if(p1!=0)$fatal(1,"opposites");
  j0=0;@(negedge clk);key=11'h775;step();if(p1!=1)$fatal(1,"key press");
  @(negedge clk);key=11'h175;step();if(p1!=0)$fatal(1,"key release");
  @(negedge clk);ba=16'h0103;ior=0;rd=0;step();if(bd!=8'h4d)$fatal(1,"I/O mask read");
  @(negedge clk);ba=16'hff05;step();if(bd!=8'h00)$fatal(1,"watchdog/no-op read baseline");
  rd=1;ww=0;#1;if(!biw)$fatal(1,"I/O write decode");step();if(biw)$fatal(1,"repeated write");
  @(negedge clk);ww=1;ior=1;step();mr=0;ww=0;ba=16'he000;#1;if(!bmw)$fatal(1,"RAM decode");
  rf=0;#1;if(bmw)$fatal(1,"refresh write");mr=1;ior=0;m1=0;#1;if(biw)$fatal(1,"ack write");
  $display("PASS clocks, downloads, malformed sessions, bus qualification, fourway/keyboard");$finish;
 end
endmodule
