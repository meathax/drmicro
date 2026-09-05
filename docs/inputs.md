# Controls

The HPS joystick layout is right,left,down,up,action,start1,start2,coin,service in bits 0..8. Both players' direction/action paths are independent. P2 start bits are combined from either pad. Opposite directions cancel; vertical wins simultaneous diagonals. This deterministic policy is not a claim to reproduce MAME's input-history four-way arbitration.

Keyboard: P1 arrows and left Ctrl; coin 5; start1 1; start2 2; service F3. P2 R/F/T/D = up/right/down/left and left Alt action. PS/2 toggle, make/break and extended bits are decoded. Reset clears latched keyboard state; held pad inputs are gated during reset and reflect current HPS state on release.

DSW1=4d and DSW2=00 come from the generated manifest. Every option, including unused switches, appears in the MRA DIP page. DIP updates arrive at ioctl index 254, addresses 0/1. They do not enter the ROM loader or reset the game. Cabinet mode and DIP flip are software-visible inputs; the CPU writes the actual game flip latch. HDMI orientation is separate: ROT270 is one counter-clockwise presentation rotation. Native/direct video remains available for a rotated monitor.
