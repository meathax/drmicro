// SPDX-License-Identifier: GPL-3.0-or-later
// Host drives pins and records observations only. All game execution is HDL.
#include "Vdrmicro_core.h"
#include "Vdrmicro_core___024root.h"
#include "Vdrmicro_core_drmicro_core.h"
#include "Vdrmicro_core_tv80s.h"
#include "Vdrmicro_core_tv80_core__M0.h"
#include "verilated.h"
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <filesystem>
#include <stdexcept>
#include <cstdlib>
static double sim_time=0;
double sc_time_stamp(){return sim_time;}
static std::vector<unsigned char> read(const std::string& p){
 std::ifstream f(p,std::ios::binary); if(!f)throw std::runtime_error("Missing payload "+p);
 return std::vector<unsigned char>((std::istreambuf_iterator<char>(f)),{});
}
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);
 std::string payload=argc>1?argv[1]:"build/drmicro.rom",out=argc>3?argv[3]:"reports/captures/smoke";
 int frames=argc>2?std::stoi(argv[2]):120;
 std::string script=argc>4?argv[4]:"attract";
 bool checkpoints=std::getenv("DRMICRO_CHECKPOINTS")!=nullptr;
 int trace_start=std::getenv("DRMICRO_TRACE_START")?std::atoi(std::getenv("DRMICRO_TRACE_START")):0;
 int trace_end=std::getenv("DRMICRO_TRACE_END")?std::atoi(std::getenv("DRMICRO_TRACE_END")):3;
 auto rom=read(payload);std::filesystem::create_directories(out);
 Vdrmicro_core d;
 uint64_t cycles=0,io=0,mw=0,fetch=0,nmis=0;bool lastfetch=false,lastnmi=false;
 auto tick=[&](){d.clk=0;sim_time+=10;d.eval();d.clk=1;sim_time+=10;d.eval();++cycles;};
 d.cold_reset=1;d.game_reset=0;d.download=0;d.ioctl_wr=0;d.ioctl_index=0;d.ioctl_addr=0;d.ioctl_data=0;
 d.joy0=0;d.joy1=0;d.ps2_key=0;d.dip1=0x4d;d.dip2=0;
 if(script=="dips"){d.dip1=0xcf;d.dip2=1;}
 if(script=="service")d.dip1=0x6d;
 if(script=="cocktail")d.dip1=0x0d;
 for(int i=0;i<64;++i)tick();d.cold_reset=0;tick();
 d.download=1;tick();
 for(size_t i=0;i<rom.size();++i){d.ioctl_addr=i;d.ioctl_data=rom[i];d.ioctl_wr=1;tick();d.ioctl_wr=0;tick();}
 d.download=0;tick();tick();
 if(!d.loaded||d.load_error)throw std::runtime_error("Real loader rejected payload");
 for(int i=0;!d.running&&i<20000;++i)tick();
 if(!d.running)throw std::runtime_error("CPU held after loading/clear");
 if(script=="stress"){
  auto reload=[&](){d.ioctl_index=0;d.download=1;tick();for(size_t i=0;i<rom.size();++i){d.ioctl_addr=i;d.ioctl_data=rom[i];d.ioctl_wr=1;tick();d.ioctl_wr=0;tick();}d.download=0;tick();tick();for(int i=0;!d.running&&i<20000;++i)tick();if(!d.running||d.load_error)throw std::runtime_error("redownload failed");};
  for(int pass=0;pass<3;++pass){
   d.ioctl_index=254;d.download=1;tick();d.ioctl_addr=0;d.ioctl_data=0xcd;d.ioctl_wr=1;tick();d.ioctl_wr=0;tick();d.download=0;tick();if(!d.running||!d.loaded)throw std::runtime_error("DIP session reset gameplay");
   d.game_reset=1;for(int i=0;i<20;++i)tick();if(!d.loaded)throw std::runtime_error("game reset invalidated ROM");d.game_reset=0;for(int i=0;!d.running&&i<20000;++i)tick();if(!d.running)throw std::runtime_error("reset clear did not finish");
   d.ioctl_index=0;d.download=1;tick();d.ioctl_addr=0;d.ioctl_data=rom[0];d.ioctl_wr=1;tick();d.ioctl_wr=0;tick();d.download=0;tick();tick();if(d.loaded||d.running||!d.load_error)throw std::runtime_error("short redownload accepted");reload();
   d.cold_reset=1;for(int i=0;i<20;++i)tick();d.cold_reset=0;tick();if(d.loaded)throw std::runtime_error("cold reset did not invalidate");reload();
  }
  std::ofstream result(out+"/result.json");result<<"{\"status\":\"PASS\",\"cold_starts\":4,\"redownloads\":6,\"game_resets\":3,\"short_loads_rejected\":3,\"dip_sessions\":3}";
 std::cout<<"PASS full-core load/reset stress: 4 cold starts, 6 re-downloads, 3 game resets, 3 rejected short sessions, 3 DIP sessions\n";return 0;
 }
 std::ofstream trace(out+"/io.csv");trace<<"cycle,frame,port,data\n";
 std::ofstream bus(out+"/fetch.csv");bus<<"cycle,frame,address\n";
 unsigned control_index=0;
 std::ofstream reads(out+"/reads.csv");reads<<"cycle,frame,port,data\n";bool last_io_read=false;unsigned read_port=0;
 std::ofstream samples(out+"/audio.raw",std::ios::binary);
 std::vector<unsigned char> rgb(256*224*3);
 std::vector<uint16_t> pens(256*224);
 uint64_t audio_phase=0,active=0,frame_pixels=0;int frame=0;bool frame_seen=false;
 bool reset_done=false;
 uint64_t stop=cycles+uint64_t(frames+3)*850000;
 while(frame<frames&&cycles<stop){
  // Input schedule is explicit, observation milestones are not assumed.
  d.joy0=0;
  if(script=="reset"&&frame==240&&!reset_done){
   d.game_reset=1;for(int i=0;i<20;++i)tick();d.game_reset=0;
   for(int i=0;!d.running&&i<20000;++i)tick();
   if(!d.running||!d.loaded)throw std::runtime_error("game reset failed");
   reset_done=true;frame_seen=false;frame_pixels=0;
  }
  if(script=="play"||script=="dips"){
   if(frame>=180&&frame<183)d.joy0|=1<<7;
   if(frame>=210&&frame<213)d.joy0|=1<<5;
   if(frame>=240&&frame<330)d.joy0|=(1<<0)|(1<<4);
   if(frame>=330&&frame<400)d.joy0|=(1<<3)|(1<<4);
  }
  if(script=="two"||script=="cocktail"){
   if((frame>=180&&frame<183)||(frame>=190&&frame<193))d.joy0|=1<<7;
   if(frame>=210&&frame<213)d.joy0|=1<<6;
  }
  tick();
  bool io_read=!d.rootp->drmicro_core->iorq_n&&!d.rootp->drmicro_core->rd_n&&d.rootp->drmicro_core->m1_n;
  if(io_read)read_port=d.debug_addr&255;
  if(last_io_read&&!io_read)reads<<cycles<<','<<frame<<','<<read_port<<','<<unsigned(d.rootp->drmicro_core->di)<<'\n';
  last_io_read=io_read;
  if(d.deadline_error)throw std::runtime_error("Renderer missed scanline deadline");
  if(d.debug_io_write){++io;trace<<cycles<<','<<frame<<','<<unsigned(d.debug_addr&255)<<','<<unsigned(d.debug_data)<<'\n';
   if((d.debug_addr&255)==4){
    if(checkpoints){
     std::ofstream ram(out+"/control_"+std::to_string(control_index)+".ram",std::ios::binary);for(int k=0;k<16384;++k)ram.put(d.rootp->drmicro_core->memory__DOT__ram[k]);
     const auto* z80=d.drmicro_core->cpu->i_tv80_core;
     std::ofstream state(out+"/control_"+std::to_string(control_index)+".json");
     state<<"{\"cycle\":"<<cycles<<",\"frame\":"<<frame<<",\"pc\":"<<z80->__PVT__PC<<",\"r\":"<<unsigned(z80->__PVT__R)<<"}";
    }
    ++control_index;
   }
  }
  if(d.debug_mem_write)++mw;
  if(d.debug_fetch&&!lastfetch){++fetch;if(frame>=trace_start&&frame<trace_end)bus<<cycles<<','<<frame<<','<<unsigned(d.debug_addr)<<'\n';}
  lastfetch=d.debug_fetch;
  if(d.debug_nmi&&!lastnmi)++nmis;lastnmi=d.debug_nmi;
  audio_phase+=48000;
  if(audio_phase>=50000000){audio_phase-=50000000;int16_t a[5]={int16_t(d.psg0),int16_t(d.psg1),int16_t(d.psg2),int16_t(int16_t(d.adpcm<<4)),int16_t(d.audio)};samples.write((char*)a,sizeof a);}
  if(d.pixel_ce){
   if(!d.hblank&&!d.vblank){
    if(d.debug_x>=256||d.debug_y<16||d.debug_y>=240)throw std::runtime_error("Misaligned active coordinates");
    size_t p=(d.debug_y-16)*256+d.debug_x;
    rgb[p*3]=d.red;rgb[p*3+1]=d.green;rgb[p*3+2]=d.blue;pens[p]=d.debug_pen;
    ++active;++frame_pixels;
   }
   if(d.debug_x==0&&d.debug_y==240){
    if(frame_seen){
     if(frame_pixels!=256*224)throw std::runtime_error("Wrong active pixel count "+std::to_string(frame_pixels));
     ++frame;
     if(frame==1||frame==30||frame%60==0||frame==frames){
      std::string stem=out+"/frame_"+std::to_string(frame);
      std::ofstream ppm(stem+".ppm",std::ios::binary);ppm<<"P6\n256 224\n255\n";ppm.write((char*)rgb.data(),rgb.size());
      std::ofstream raw(stem+".pen",std::ios::binary);raw.write((char*)pens.data(),pens.size()*2);
      std::ofstream ram(stem+".ram",std::ios::binary);
      for(int k=0;k<16384;++k)ram.put(d.rootp->drmicro_core->memory__DOT__ram[k]);
      std::ofstream meta(stem+".json");meta<<"{\"flip\":"<<unsigned(d.rootp->drmicro_core->flip)<<",\"cycle\":"<<cycles<<"}";
     }
     frame_pixels=0;
    }else{frame_seen=true;frame_pixels=0;}
   }
  }
 }
 bool pass=frame==frames && (frames<30 || (io>0 && nmis>0));
 std::ofstream result(out+"/result.json");result<<"{\"status\":\""<<(pass?"PASS":"FAIL")<<"\",\"level\":\"smoke_observation\",\"frames\":"<<frame<<",\"cycles\":"<<cycles<<",\"fetches\":"<<fetch<<",\"ram_writes\":"<<mw<<",\"io_writes\":"<<io<<",\"nmi_events\":"<<nmis<<",\"script\":\""<<script<<"\"}\n";
 std::cout<<"Frames "<<frame<<" fetches "<<fetch<<" RAM writes "<<mw<<" IO writes "<<io<<" NMI "<<nmis<<"\n";
 return pass?0:1;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
