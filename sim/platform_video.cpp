// SPDX-License-Identifier: GPL-3.0-or-later
#include "Vplatform_video_top.h"
#include "verilated.h"
#include <iostream>
#include <stdexcept>
double sc_time_stamp(){return 0;}
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);
 for(int mode=0;mode<4;++mode){
  Vplatform_video_top d;d.fx=mode==3?0:mode;d.gamma_en=mode==3;
  auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();};
  // Program a deliberately non-identity LUT for the gamma-enabled case.
  d.ce=0;d.hb=1;d.vb=1;d.hs=0;d.vs=0;d.rgb=0;
  for(int i=0;i<768;++i){d.gamma_wr=1;d.gamma_addr=i;d.gamma_value=255-(i&255);tick();}
  d.gamma_wr=0;
  int checked=0,lines=0,width=0,first_x=-1;bool old_de=false;
  for(int frame=0;frame<7;++frame)for(int y=0;y<256;++y)for(int x=0;x<320;++x)for(int t=0;t<10;++t){
   d.ce=t==0;d.hb=x>=256;d.vb=y<16||y>=240;d.hs=x>=272&&x<304;d.vs=y>=244&&y<248;
   d.rgb=mode==0?((x&255)<<16)|(y<<8)|((x^y^0xa5)&255):0x397bd2;
   tick();
   if(frame>=3&&d.pce){
    if(d.de){
     if(!old_de){width=0;first_x=(d.pixel>>16)&255;}
     ++width;++checked;
     if(mode==0){int px=(d.pixel>>16)&255,py=(d.pixel>>8)&255;
      if(px!=width-1||py<16||py>=240||(d.pixel&255)!=(px^py^0xa5))throw std::runtime_error("native coordinate/color corruption");
     }else if(width>12&&width<240){
      unsigned expected=mode==3?0xc6842d:0x397bd2;
      if(d.pixel!=expected)throw std::runtime_error("scandoubler/HQ2x/gamma color corruption");
     }
    }
    if(!d.de&&old_de){
     int expected=mode==1?512:256;
     if(width!=expected)throw std::runtime_error("platform line width "+std::to_string(width)+" expected "+std::to_string(expected));
     ++lines;
    }
    old_de=d.de;
   }
  }
  int expected_lines=(mode==1||mode==2)?4*448:4*224;
  if(lines!=expected_lines)throw std::runtime_error("platform line count "+std::to_string(lines)+" expected "+std::to_string(expected_lines));
  std::cout<<"PASS real arcade_video mode="<<mode<<" pixels="<<checked<<" lines="<<lines<<" (native, HQ2x, scandoubler, gamma respectively)\n";
  d.final();
 }
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
