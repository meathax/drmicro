// SPDX-License-Identifier: GPL-3.0-or-later
#include "Vscreen_rotate.h"
#include "verilated.h"
#include <stdexcept>
#include <iostream>
static double t=0;double sc_time_stamp(){return t;}
int main(){try{
 Vscreen_rotate d;int frame=0,writes=0;
 d.CE_PIXEL=0;d.VGA_R=0;d.VGA_G=0;d.VGA_B=0;d.VGA_HS=0;d.VGA_VS=0;d.VGA_DE=0;
 d.rotate_ccw=1;d.no_rotate=0;d.flip=0;d.FB_VBL=0;d.FB_LL=1;d.DDRAM_BUSY=0;
 auto tick=[&](){d.CLK_VIDEO=0;d.eval();t+=10;d.CLK_VIDEO=1;d.eval();t+=10;
  if(d.DDRAM_WE&&frame>=7&&!d.no_rotate){
   if(d.FB_WIDTH!=6||d.FB_HEIGHT!=8||d.FB_STRIDE!=32)throw std::runtime_error("dimensions");
   if(d.DDRAM_BE!=15&&d.DDRAM_BE!=240)throw std::runtime_error("byte lanes");
   int offset=(d.DDRAM_ADDR&0xfffff)*8+(d.DDRAM_BE==240?4:0),x=offset%32/4,y=offset/32;
   int sx=(d.DDRAM_DIN&255)-1,sy=((d.DDRAM_DIN>>8)&255)-1;
   if(x!=sy||y!=7-sx)throw std::runtime_error("CCW coordinate mapping");++writes;
  }
 };
 auto pixel=[&](int x,int y){d.VGA_DE=x<8&&y<6;d.VGA_HS=x==10;d.VGA_VS=y==8;d.FB_VBL=d.VGA_VS;d.VGA_R=x+1;d.VGA_G=y+1;d.VGA_B=x+16*y;d.CE_PIXEL=1;tick();d.CE_PIXEL=0;for(int i=0;i<9;++i)tick();};
 for(frame=0;frame<9;++frame)for(int y=0;y<10;++y)for(int x=0;x<12;++x)pixel(x,y);
 if(writes!=96)throw std::runtime_error("write count "+std::to_string(writes));
 d.no_rotate=1;
 for(frame=0;frame<5;++frame)for(int y=0;y<10;++y)for(int x=0;x<12;++x)pixel(x,y);
 if(d.FB_EN||d.video_rotated)throw std::runtime_error("native bypass");
 std::cout<<"PASS: 96 asymmetric labelled pixels CCW, stride, byte lanes, native bypass; always-ready DDR sink, two-state initialization\n";
 d.final();return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
