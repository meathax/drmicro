// SPDX-License-Identifier: GPL-3.0-or-later
#include "Vplatform_hps_top.h"
#include "verilated.h"
#include <fstream>
#include <iostream>
#include <vector>
#include <stdexcept>
double sc_time_stamp(){return 0;}
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);Vplatform_hps_top d;
 auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();};
 auto settle=[&](){for(int i=0;i<5;++i)tick();};
 d.reset=1;d.strobe=0;d.io_enable=0;d.fp_enable=0;d.host_data=0;settle();d.reset=0;settle();
 auto word=[&](unsigned value){d.host_data=value;d.strobe=1;tick();d.strobe=0;settle();};
 auto command=[&](bool fp,unsigned cmd,std::vector<unsigned> data){
  d.fp_enable=fp;d.io_enable=!fp;word(cmd);for(auto v:data)word(v);d.fp_enable=0;d.io_enable=0;settle();
 };
 command(false,1,{0});command(false,0x1e,{0,0,0,0,0,0,0,0});command(false,2,{0,0});command(false,3,{0,0});
 std::ifstream f("build/drmicro.rom",std::ios::binary);if(!f)throw std::runtime_error("ROM payload missing");
 std::vector<unsigned char> rom((std::istreambuf_iterator<char>(f)),{});
 auto download=[&](unsigned index,const std::vector<unsigned char>&bytes){
  command(true,0x55,{index});command(true,0x53,{1});
  d.fp_enable=1;word(0x54);for(auto v:bytes)word(v);d.fp_enable=0;settle();command(true,0x53,{0});
 };
 download(0,{rom[0]});if(d.loaded||!d.error)throw std::runtime_error("short HPS load accepted");
 download(0,rom);for(int i=0;i<20000&&!d.running;++i)tick();
 if(!d.loaded||!d.running||d.error)throw std::runtime_error("HPS full download failed");
 download(254,{0xcf,1});if(d.dip1!=0xcf||d.dip2!=1||!d.running)throw std::runtime_error("HPS DIP transport/reset isolation failed");
 command(false,2,{(1<<7)|(1<<4)|(1<<0),0});
 if(d.p1!=0x32)throw std::runtime_error("HPS joystick mapping failed");
 command(false,2,{0,0});command(false,3,{(1<<3)|(1<<4),0});
 if(d.p2!=0x11)throw std::runtime_error("HPS second joystick mapping failed");
 command(false,3,{0,0});
 command(false,5,{0xe0,0x75});if(d.p1!=1)throw std::runtime_error("HPS PS2 make failed");
 command(false,5,{0xe0,0xf0,0x75});if(d.p1!=0)throw std::runtime_error("HPS PS2 break failed");
 command(false,0x1e,{4,0,0,0,0,0,0,0});if(d.arx!=4||d.ary!=3)throw std::runtime_error("native aspect/status mapping");
 command(false,0x1e,{0,0,0,0,0,0,0,0});if(d.arx!=3||d.ary!=4)throw std::runtime_error("portrait aspect/status mapping");
 command(false,0x1e,{1,0,0,0,0,0,0,0});if(d.running||!d.loaded)throw std::runtime_error("OSD reset state");
 command(false,0x1e,{0,0,0,0,0,0,0,0});for(int i=0;i<20000&&!d.running;++i)tick();
 int fetches=0;bool old=false;for(int i=0;i<100000;++i){tick();if(d.fetch&&!old)++fetches;old=d.fetch;}
 if(!d.running||fetches<100)throw std::runtime_error("wrapper CPU did not resume");
 std::cout<<"PASS actual emu/hps_io: malformed/full ROM download, DIP isolation, both gamepads, PS2 make/break, aspect/status and reset; CPU fetches="<<fetches<<"\n";
 d.final();return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
