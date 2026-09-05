`timescale 1ns/1ps
module tb_cpu_refresh;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;wire ce;drmicro_ce #(.RATE(3),.CLOCK(50)) divider(clk,reset,ce);
 wire[15:0]addr;wire[7:0]dout,di;reg[7:0]md;reg[7:0]mem[0:65535];
 wire mr,io,rd,wr,rf,m1,halt,mw,iw;
 tv80s cpu(.clk(clk),.cen(ce),.reset_n(!reset),.wait_n(1'b1),.int_n(1'b1),.nmi_n(1'b1),.busrq_n(1'b1),.di(di),.dout(dout),.A(addr),.mreq_n(mr),.iorq_n(io),.rd_n(rd),.wr_n(wr),.rfsh_n(rf),.m1_n(m1),.halt_n(halt),.busak_n());
 drmicro_bus bus(clk,reset,mr,io,rd,wr,rf,m1,addr,md,8'h00,8'h00,8'h4d,8'h00,di,mw,iw);
 integer refreshes=0;reg old_rf=1;
 always @(posedge clk)begin md<=mem[addr];if(mw)mem[addr]<=dout;end
 always @(negedge clk)begin if(!rf&&old_rf)refreshes=refreshes+1;old_rf=rf;end
 initial begin
  for(integer i=0;i<65536;i=i+1)mem[i]=0;
  // LD R,fe; NOP; LD A,R -> 81: low seven bits wrap, high bit persists.
  // Save AF to BC to check LD A,R flags use R, not the zero-valued I register.
  {mem[0],mem[1],mem[2],mem[3],mem[4],mem[5],mem[6],mem[7],mem[8],mem[9],mem[10],mem[11],mem[12],mem[13],mem[14],mem[15],mem[16],mem[17],mem[18],mem[19]}=
   160'h3100ff3efeed4f00ed5f3200c0f5c1ed4302c076;
  // LD R,26; LD A,R -> 28 must copy both undocumented X/Y flag bits.
  {mem[19],mem[20],mem[21],mem[22],mem[23],mem[24],mem[25],mem[26],mem[27],mem[28],mem[29],mem[30],mem[31]}=104'h3e26ed4fed5ff5c1ed4304c076;
  repeat(4)@(negedge clk);reset=0;repeat(5000)@(negedge clk);
  if(mem[16'hc000]!==8'h81||mem[16'hc003]!==8'h81||mem[16'hc002][7:1]!==7'h40)$fatal(1,"LD A,R value/flags: A=%h F=%h",mem[16'hc000],mem[16'hc002]);
  if(mem[16'hc005]!==8'h28||mem[16'hc004]!=={7'h14,mem[16'hc002][0]})$fatal(1,"LD A,R X/Y flags and preserved carry: A=%h F=%h",mem[16'hc005],mem[16'hc004]);
  if(refreshes<20||halt!==0)$fatal(1,"refresh cycles must continue during HALT");
  $display("PASS LD R,A; LD A,R value/flags, seven-bit wrap, prefix increments and HALT refresh");$finish;
 end
endmodule
