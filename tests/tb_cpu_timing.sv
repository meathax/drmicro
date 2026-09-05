`timescale 1ns/1ps
// Zilog UM0080 instruction timing, measured between successive M1 reads.
module tb_cpu_timing;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;wire ce;drmicro_ce #(.RATE(3),.CLOCK(50)) divider(clk,reset,ce);
 wire[15:0]addr;wire[7:0]dout,di;reg[7:0]md;reg[7:0]mem[0:65535];
 wire mr,io,rd,wr,rf,m1,halt,mw,iw;
 tv80s cpu(.clk(clk),.cen(ce),.reset_n(!reset),.wait_n(1'b1),.int_n(1'b1),.nmi_n(1'b1),.busrq_n(1'b1),.di(di),.dout(dout),.A(addr),.mreq_n(mr),.iorq_n(io),.rd_n(rd),.wr_n(wr),.rfsh_n(rf),.m1_n(m1),.halt_n(halt),.busak_n());
 drmicro_bus bus(clk,reset,mr,io,rd,wr,rf,m1,addr,md,8'h37,8'h00,8'h4d,8'h00,di,mw,iw);
 integer ticks=0,last_tick=0,n=0;reg oldfetch=0;wire fetch=!m1&&!mr&&!rd;
 integer expected[0:7];
 always @(posedge clk)begin
  md<=mem[addr];if(mw)mem[addr]<=dout;if(ce&&!reset)ticks=ticks+1;
 end
 always @(negedge clk)if(!reset)begin
  if(fetch&&!oldfetch)begin
   if(n>0)begin
    $display("M1 address=%h interval=%0d expected=%0d",addr,ticks-last_tick,expected[n-1]);
    if(ticks-last_tick!=expected[n-1])$fatal(1,"Z80 instruction cycle mismatch");
   end
   last_tick=ticks;n=n+1;
   if(n==9)begin $display("PASS Z80 LD A,n=7, OUT(n),A=11, IN A,(n)=11, NOP=4, LD SP=10, CALL=17, RET=10 T states");$finish;end
  end
  oldfetch=fetch;
 end
 initial begin
  for(integer i=0;i<65536;i=i+1)mem[i]=0;
  mem[0]=8'h3e;mem[1]=8'h55;mem[2]=8'hd3;mem[3]=0;
  mem[4]=8'hd3;mem[5]=0;mem[6]=8'hdb;mem[7]=0;mem[8]=0;
  mem[9]=8'h31;mem[10]=0;mem[11]=8'hff;mem[12]=8'hcd;mem[13]=32;mem[14]=0;mem[15]=8'h76;mem[32]=8'hc9;
  expected[0]=7;expected[1]=11;expected[2]=11;expected[3]=11;expected[4]=4;
  expected[5]=10;expected[6]=17;expected[7]=10;
  repeat(4)@(negedge clk);reset=0;
  repeat(20000)@(negedge clk);$fatal(1,"timeout");
 end
endmodule
