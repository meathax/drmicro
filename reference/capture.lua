-- SPDX-License-Identifier: GPL-3.0-or-later
-- Documented MAME 0.289 APIs. Checker side only; no part of the hardware DUT.
-- Autoboot scripts can be invoked again after a soft reset; retain the first
-- callback and its monotonically increasing frame counter.
if drmicro_capture_installed then return end
drmicro_capture_installed=true
local machine=manager.machine
local cpu=machine.devices[':maincpu']
local memory=cpu.spaces['program']
local ios=cpu.spaces['io']
local screen=machine.screens[':screen']
local out=os.getenv('DRMICRO_REFERENCE_OUT') or 'reports/captures/mame_attract'
local script=os.getenv('DRMICRO_SCRIPT') or 'attract'
local frames=tonumber(os.getenv('DRMICRO_FRAMES') or '120')
local frame=0
-- Both schedules now use the frame-boundary NMI profile. Offset remains
-- configurable for reproducing the earlier NMI_LINE=240 experiment.
local input_offset=tonumber(os.getenv('DRMICRO_REFERENCE_INPUT_OFFSET') or '0')
local trace_start=tonumber(os.getenv('DRMICRO_TRACE_START') or '13')
local trace_end=tonumber(os.getenv('DRMICRO_TRACE_END') or '16')
local flip=0
local control_index=0
local checkpoints=os.getenv('DRMICRO_CHECKPOINTS')~=nil
-- Optional boundary trace: capture the reference CPU at MAME's completed-frame
-- callback, which is the point where the driver schedules its vblank NMI.
local frame_state=nil
if os.getenv('DRMICRO_FRAME_STATE') then
 frame_state=assert(io.open(out..'/frame_state.csv','w'))
 frame_state:write('frame,time,pc,r\n')
end
local log=assert(io.open(out..'/io.csv','w'))
log:write('time,frame,port,data\n')
local reads=assert(io.open(out..'/reads.csv','w'));reads:write('time,frame,port,data\n')
drmicro_read_tap=ios:install_read_tap(0,255,'drmicro_reads',function(address,data,mask)
 reads:write(string.format('%.12f,%d,%d,%d\n',machine.time:as_double(),frame,address,data))
end)
drmicro_tap=ios:install_write_tap(0,255,'drmicro_io',function(address,data,mask)
 log:write(string.format('%.12f,%d,%d,%d\n',machine.time:as_double(),frame,address,data))
 if address==4 then
  flip=(data>>1)&1
  if checkpoints then
   local f=assert(io.open(out..'/control_'..control_index..'.ram','wb'));f:write(memory:read_range(0xc000,0xffff,8));f:close()
   f=assert(io.open(out..'/control_'..control_index..'.json','w'))
   f:write(string.format('{"frame":%d,"pc":%d,"r":%d,"time":%.12f}',frame,cpu.state['PC'].value,cpu.state['R'].value,machine.time:as_double()));f:close()
  end
  control_index=control_index+1
 end
end)
local function field(port,mask,value) machine.ioport.ports[port]:field(mask):set_value(value and 1 or 0) end
-- Reset every DIP explicitly: -noreadconfig alone does not suppress saved
-- per-game .cfg input settings left by a preceding test case.
for _,pair in ipairs({{3,1},{4,4},{24,8},{32,0},{64,64},{128,0}}) do machine.ioport.ports[':DSW1']:field(pair[1]).user_value=pair[2] end
for _,mask in ipairs({7,8,16,32,64,128}) do machine.ioport.ports[':DSW2']:field(mask).user_value=0 end
if script=='dips' then
 machine.ioport.ports[':DSW1']:field(3).user_value=3
 machine.ioport.ports[':DSW1']:field(128).user_value=128
 machine.ioport.ports[':DSW2']:field(7).user_value=1
elseif script=='service' then machine.ioport.ports[':DSW1']:field(32).user_value=32
elseif script=='cocktail' then machine.ioport.ports[':DSW1']:field(64).user_value=0 end
emu.register_frame_done(function()
 frame=frame+1
 if frame_state then
  frame_state:write(string.format('%d,%.12f,%d,%d\n',frame,machine.time:as_double(),cpu.state['PC'].value,cpu.state['R'].value))
 end
 local input_frame=frame-input_offset
 if os.getenv('DRMICRO_DEBUG_TRACE') then
  if frame==trace_start then machine.debugger:command('trace '..out..'/instructions.txt,maincpu,noloop,{tracelog "T=%d ",totalcycles}') end
  if frame==trace_end then machine.debugger:command('trace off,maincpu') end
 end
 if script=='reset' and frame==240 then machine:soft_reset() end
 if script=='play' or script=='dips' then
  field(':P1',32,input_frame>=180 and input_frame<183)
  field(':P2',32,input_frame>=210 and input_frame<213)
  field(':P1',2,input_frame>=240 and input_frame<330)
  field(':P1',1,input_frame>=330 and input_frame<400)
  field(':P1',16,input_frame>=240 and input_frame<400)
 elseif script=='two' or script=='cocktail' then
  field(':P1',32,(input_frame>=180 and input_frame<183)or(input_frame>=190 and input_frame<193))
  field(':P2',64,input_frame>=210 and input_frame<213)
 end
 if frame==1 or frame==30 or frame%60==0 or frame==frames then
  local stem=out..'/frame_'..frame
  local f=assert(io.open(stem..'.ram','wb'));f:write(memory:read_range(0xc000,0xffff,8));f:close()
  local pixels,w,h=screen:pixels()
  f=assert(io.open(stem..'.pixels','wb'));f:write(pixels);f:close()
  f=assert(io.open(stem..'.json','w'));f:write(string.format('{"flip":%d,"width":%d,"height":%d,"pc":%d,"time":%.12f}',flip,w,h,cpu.state['PC'].value,machine.time:as_double()));f:close()
  screen:snapshot('frame_'..frame..'.png')
 end
 if frame>=frames then
  log:flush();reads:flush();if frame_state then frame_state:flush() end
  local f=assert(io.open(out..'/completion.json','w'));f:write(string.format('{"frames":%d,"script":"%s"}',frame,script));f:close()
  machine:exit()
 end
end,'frame')
print('DrMicro reference capture installed; script='..script..'; input callback offset='..input_offset)
