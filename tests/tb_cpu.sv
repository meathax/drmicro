`timescale 1ns/1ps
module tb_cpu;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,nmi=1;wire ce;drmicro_ce #(.RATE(3),.CLOCK(50)) divider(clk,reset,ce);
 wire[15:0]addr;wire[7:0]dout,di;reg[7:0]md;reg[7:0]mem[0:65535];
 wire mr,io,rd,wr,rf,m1,halt,mw,iw;
 tv80s cpu(.clk(clk),.cen(ce),.reset_n(!reset),.wait_n(1'b1),.int_n(1'b1),.nmi_n(nmi),.busrq_n(1'b1),.di(di),.dout(dout),.A(addr),.mreq_n(mr),.iorq_n(io),.rd_n(rd),.wr_n(wr),.rfsh_n(rf),.m1_n(m1),.halt_n(halt),.busak_n());
 drmicro_bus bus(clk,reset,mr,io,rd,wr,rf,m1,addr,md,8'h37,8'h00,8'h4d,8'h00,di,mw,iw);
 integer ios=0,nmis=0;
 always @(posedge clk)begin
  md<=mem[addr];if(mw)mem[addr]<=dout;
  if(iw)begin if(addr[7:0]!=2||dout!=8'h37)$fatal(1,"I/O diagnostic");ios<=ios+1;end
 end
 initial begin
  for(integer i=0;i<65536;i=i+1)mem[i]=0;
  // LD SP,ff00; LD A,5a; LD (c000),A; IN A,(0); OUT (2),A;
  // LD HL,c000; INC (HL); HALT; JP 0010. NMI writes c001 and RETN.
  mem[0]=8'h31;mem[1]=0;mem[2]=8'hff;mem[3]=8'h3e;mem[4]=8'h5a;
  mem[5]=8'h32;mem[6]=0;mem[7]=8'hc0;mem[8]=8'hdb;mem[9]=0;
  mem[10]=8'hd3;mem[11]=2;mem[12]=8'h21;mem[13]=0;mem[14]=8'hc0;
  mem[15]=8'h34;mem[16]=8'h76;mem[17]=8'hc3;mem[18]=16;mem[19]=0;
  mem[102]=8'h3e;mem[103]=8'ha5;mem[104]=8'h32;mem[105]=1;mem[106]=8'hc0;
  mem[107]=8'hed;mem[108]=8'h45;
  repeat(4)@(negedge clk);reset=0;
  repeat(6000)@(negedge clk);
  if(mem[16'hc000]!=8'h5b||ios!=1||halt!==0)$fatal(1,"TV80 diagnostic before NMI RAM=%h IO=%d halt=%b",mem[16'hc000],ios,halt);
  nmi=0;repeat(40)@(negedge clk);nmi=1;
  repeat(6000)@(negedge clk);
  if(mem[16'hc001]!=8'ha5||ios!=1||halt!==0)$fatal(1,"TV80 NMI/RETN diagnostic");
  $display("PASS real TV80 CE, opcodes/data, sync reads, RMW, IO once, HALT/NMI/RETN");$finish;
 end
endmodule
