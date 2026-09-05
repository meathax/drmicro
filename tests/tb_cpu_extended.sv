`timescale 1ns/1ps
// Zilog UM0080 T states: branches, block transfers, indexed and ED/CB ops.
module tb_cpu_extended;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;wire ce;drmicro_ce #(.RATE(3),.CLOCK(50)) divider(clk,reset,ce);
 wire[15:0]addr;wire[7:0]dout,di;reg[7:0]md;reg[7:0]mem[0:65535];
 wire mr,io,rd,wr,rf,m1,halt,mw,iw;
 tv80s cpu(.clk(clk),.cen(ce),.reset_n(!reset),.wait_n(1'b1),.int_n(1'b1),.nmi_n(1'b1),.busrq_n(1'b1),.di(di),.dout(dout),.A(addr),.mreq_n(mr),.iorq_n(io),.rd_n(rd),.wr_n(wr),.rfsh_n(rf),.m1_n(m1),.halt_n(halt),.busak_n());
 drmicro_bus bus(clk,reset,mr,io,rd,wr,rf,m1,addr,md,8'h00,8'h00,8'h4d,8'h00,di,mw,iw);
 integer ticks=0,last_tick=0,n=0,count=0;reg oldfetch=0,skip_prefix=0;wire fetch=!m1&&!mr&&!rd;
 integer pcs[0:63],duration[0:63];
 task expected(input integer pc,input integer t);begin pcs[count]=pc;duration[count]=t;count=count+1;end endtask
 task bytes(input integer pc,input integer len,input[63:0]data);begin
  for(integer i=0;i<len;i=i+1)mem[pc+i]=8'(data>>((len-1-i)*8));
 end endtask
 always @(posedge clk)begin md<=mem[addr];if(mw)mem[addr]<=dout;if(ce&&!reset)ticks=ticks+1;end
 always @(negedge clk)if(!reset)begin
  if(fetch&&!oldfetch)begin
   if(skip_prefix)skip_prefix=0;
   else begin
    if(addr!=pcs[n])$fatal(1,"instruction %0d PC %h expected %h",n,addr,pcs[n]);
    if(n>0&&ticks-last_tick!=duration[n-1])$fatal(1,"PC %h: previous instruction took %0d expected %0d",addr,ticks-last_tick,duration[n-1]);
    last_tick=ticks;n=n+1;
    if(n==count)begin
     if(mem[16'hc100]!=8'h12||mem[16'hc101]!=8'h34||mem[16'hc203]!=8'h55)$fatal(1,"block/indexed transfer results");
     $display("PASS extended Z80 cycles: DJNZ/JR taken and untaken, LDIR repeat/final, indexed loads, CB, stack, LD A,R and conditional RET");$finish;
    end
    if(mem[addr]==8'hed||mem[addr]==8'hdd||mem[addr]==8'hcb)skip_prefix=1;
   end
  end
  oldfetch=fetch;
 end
 initial begin
  for(integer i=0;i<65536;i=i+1)mem[i]=0;
  mem[16'hc000]=8'h12;mem[16'hc001]=8'h34;
  bytes(0,3,24'h3100ff);bytes(3,2,16'h0602);bytes(5,2,16'h10fe);bytes(7,1,8'haf);
  bytes(8,2,16'h2000);bytes(10,2,16'h2800);bytes(12,3,24'h2100c0);bytes(15,3,24'h1100c1);
  bytes(18,3,24'h010200);bytes(21,2,16'hedb0);bytes(23,4,32'hdd2100c2);
  bytes(27,4,32'hdd360355);bytes(31,3,24'hdd7e03);bytes(34,2,16'hcb07);
  bytes(36,1,8'hf5);bytes(37,1,8'hd1);bytes(38,2,16'hed5f);
  bytes(40,3,24'hcd4000);bytes(43,3,24'hcd4100);bytes(46,1,8'h76);
  bytes(64,3,24'hc0c8c9);
  expected(0,10);expected(3,7);expected(5,13);expected(5,8);expected(7,4);
  expected(8,7);expected(10,12);expected(12,10);expected(15,10);expected(18,10);
  expected(21,21);expected(21,16);expected(23,14);expected(27,19);expected(31,19);
  expected(34,8);expected(36,11);expected(37,10);expected(38,9);expected(40,17);
  expected(64,11);expected(43,17);expected(65,5);expected(66,10);expected(46,4);
  repeat(4)@(negedge clk);reset=0;
  repeat(20000)@(negedge clk);$fatal(1,"timeout");
 end
endmodule
