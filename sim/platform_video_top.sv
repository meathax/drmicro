// SPDX-License-Identifier: GPL-3.0-or-later
// Test boundary: real pinned arcade_video and downstream video logic.
module platform_video_top(
 input clk,ce,hb,vb,hs,vs,
 input [23:0] rgb,
 input [2:0] fx,
 input gamma_en,gamma_wr,
 input [9:0] gamma_addr,
 input [7:0] gamma_value,
 output pce,de,ohs,ovs,
 output [23:0] pixel
);
 wire [21:0] gamma_bus;
 assign gamma_bus[20:0]={clk,gamma_en,gamma_wr,gamma_addr,gamma_value};
 arcade_video #(.WIDTH(256),.DW(24),.GAMMA(1)) dut(
  .clk_video(clk),.ce_pix(ce),.RGB_in(rgb),.HBlank(hb),.VBlank(vb),.HSync(hs),.VSync(vs),
  .CLK_VIDEO(),.CE_PIXEL(pce),.VGA_R(pixel[23:16]),.VGA_G(pixel[15:8]),.VGA_B(pixel[7:0]),
  .VGA_HS(ohs),.VGA_VS(ovs),.VGA_DE(de),.VGA_SL(),.fx(fx),.forced_scandoubler(1'b0),.gamma_bus(gamma_bus));
endmodule
