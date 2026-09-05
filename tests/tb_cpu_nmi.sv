`timescale 1ns/1ps
module tb_cpu_nmi;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,nmi=1;wire ce;drmicro_ce #(.RATE(3),.CLOCK(50)) divider(clk,reset,ce);
 wire[15:0]addr;wire[7:0]dout,di;reg[7:0]md;reg[7:0]mem[0:65535];
 wire mr,io,rd,wr,rf,m1,halt,mw,iw;
 tv80s cpu(.clk(clk),.cen(ce),.reset_n(!reset),.wait_n(1'b1),.int_n(1'b1),.nmi_n(nmi),.busrq_n(1'b1),.di(di),.dout(dout),.A(addr),.mreq_n(mr),.iorq_n(io),.rd_n(rd),.wr_n(wr),.rfsh_n(rf),.m1_n(m1),.halt_n(halt),.busak_n());
 drmicro_bus bus(clk,reset,mr,io,rd,wr,rf,m1,addr,md,8'h00,8'h00,8'h4d,8'h00,di,mw,iw);
 integer ticks=0,entry=0;reg old_nmic=0,checked=0;
 always @(posedge clk)begin md<=mem[addr];if(mw)mem[addr]<=dout;if(ce&&!reset)ticks=ticks+1;end
 always @(negedge clk)if(!reset)begin
  if(cpu.i_tv80_core.NMICycle&&!old_nmic)entry=ticks;
  old_nmic=cpu.i_tv80_core.NMICycle;
  if(!checked&&entry>0&&!m1&&!mr&&!rd&&addr==16'h66)begin
   $display("NMI entry latency=%0d T states",ticks-entry);
   if(ticks-entry!=11)$fatal(1,"Zilog NMI must be 5+3+3 T states");
   checked=1;
  end
 end
 initial begin
  for(integer i=0;i<65536;i=i+1)mem[i]=0;
  mem[0]=8'h31;mem[1]=0;mem[2]=8'hff;mem[3]=8'h76;mem[4]=8'h76;
  mem[102]=8'hed;mem[103]=8'h45;
  repeat(4)@(negedge clk);reset=0;repeat(1000)@(negedge clk);
  nmi=0;repeat(40)@(negedge clk);nmi=1;repeat(2000)@(negedge clk);
  if(!checked||halt!==0||mem[16'hfefe]!==4||mem[16'hfeff]!==0)$fatal(1,"NMI stack/RETN");
  $display("PASS NMI 11 T-state entry, HALT wake, return PC and RETN");$finish;
 end
endmodule
