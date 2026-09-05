// SPDX-License-Identifier: GPL-3.0-or-later
// Actual emu and hps_io. The host-side bus master and always-ready DDR input
// represent platform boundaries; no game/download/control logic is replaced.
module platform_hps_top(
 input clk,reset,strobe,io_enable,fp_enable,
 input [15:0] host_data,
 output [15:0] host_return,
 output loaded,running,error,fetch,
 output [7:0] dip1,dip2,p1,p2,
 output [10:0] key,
 output [12:0] arx,ary
);
 wire [45:0] bus;
 assign bus[45:38]=8'd0;
 assign bus[35:33]={fp_enable,io_enable,strobe};
 assign bus[31:16]=host_data;
 assign host_return=bus[15:0];
 emu dut(.CLK_50M(clk),.RESET(reset),.HPS_BUS(bus),.CLK_AUDIO(clk),
  .HDMI_WIDTH(12'd1920),.HDMI_HEIGHT(12'd1080),.FB_VBL(1'b0),.FB_LL(1'b0),
  .SD_MISO(1'b1),.SD_CD(1'b0),.DDRAM_BUSY(1'b0),.DDRAM_DOUT(64'd0),.DDRAM_DOUT_READY(1'b0),
  .UART_CTS(1'b0),.UART_RXD(1'b0),.UART_DSR(1'b0),.USER_IN(7'h7f),.OSD_STATUS(1'b0),
  .VIDEO_ARX(arx),.VIDEO_ARY(ary));
 assign loaded=dut.loaded;assign running=dut.running;assign error=dut.load_error;
 assign dip1=dut.dip1;assign dip2=dut.dip2;assign p1=dut.board.p1;assign p2=dut.board.p2;
 assign fetch=dut.board.debug_fetch;assign key=dut.ps2_key;
endmodule
