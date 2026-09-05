# Dr. Micro hardware specification

Functional baseline: MAME commit `5fdbebde74ce2cb4db89ae615860c51a1bbf1f38`. The complete driver is retained in `reference/mame/src/mame/sanritsu/drmicro.cpp`. Source line numbers below refer to that immutable revision. This is an emulation-derived specification, not a PCB timing measurement.

## CPU and address maps

One Z80, normal mode, 18.432 MHz / 6 = 3.072 MHz (source marks this clock with a question). Three SN76496 share this nominal input rate. MSM5205 input 384 kHz, S64_4B = 6 kHz. Refresh is 60 Hz, 256×256 logical pixels, visible x=0..255, y=16..239. ROT270 at presentation. Source: [427–469](https://github.com/mamedev/mame/blob/5fdbebde74ce2cb4db89ae615860c51a1bbf1f38/src/mame/sanritsu/drmicro.cpp#L427-L469).

| Program address | Behaviour |
|---|---|
| 0000–bfff | Six 8 KiB program ROMs, read only |
| c000–dfff | 8 KiB work RAM |
| e000–e7ff | Video RAM 1, 2 KiB |
| e800–efff | Video RAM 0, 2 KiB |
| f000–ffff | 4 KiB work RAM |

I/O addresses use the low eight bits. Reads 00=P1, 01=P2, 03=DSW1, 04=DSW2. Writes 00/01/02=SN1/SN2/SN3, 03=sample start, 04=control. Read port 02 and unmapped reads return ff in the implementation. Port 05 reads 00, matching MAME noprw, and ignores writes; no speculative watchdog is present. Map: [260–283](https://github.com/mamedev/mame/blob/5fdbebde74ce2cb4db89ae615860c51a1bbf1f38/src/mame/sanritsu/drmicro.cpp#L260-L283).

## Graphics and palette

For each layer, bytes 000–3ff hold tile codes and 400–7ff attributes. Code = byte + ((attribute & c0) << 2), colour = attribute & 0f, X/Y flip = bits 4/5. Tilemap scan is row-major 32×32, 8×8 tiles. Draw BG0 opaque, BG1 pen 0 transparent, then sprite bank 0 and bank 1. Tile and sprite descriptions: [95–209](https://github.com/mamedev/mame/blob/5fdbebde74ce2cb4db89ae615860c51a1bbf1f38/src/mame/sanritsu/drmicro.cpp#L95-L209).

Eight four-byte sprite records per video bank are at offsets 00,04,..1c of that same video RAM. Record bytes are Y, character, attribute, X. Code=(character>>2)|(attribute&c0). Local X/Y flips are character bits 0/1 XOR game flip. Without game flip Y=(240-Y)&ff; with flip X=(240-X)&ff. Draw each 16×16 sprite, ascending record order, pen 0 transparent. X>240 has a second copy at X-256; Y is clipped, not wrapped. Later opaque pixels overwrite; transparent pixels never own a pixel.

MAME layouts: [354–408](https://github.com/mamedev/mame/blob/5fdbebde74ce2cb4db89ae615860c51a1bbf1f38/src/mame/sanritsu/drmicro.cpp#L354-L408).

| Layout | Count | Planes, in significance order (bit offsets) | X bit offsets | Y bit offsets | Code stride |
|---|---:|---|---|---|---:|
| 2bpp tile | 1024 | 0, 0x10000 | 7..0 | 0,8,..56 | 64 bits |
| 3bpp tile | 1024 | 0x20000,0x10000,0 | 7..0 | 0,8,..56 | 64 bits |
| 2bpp sprite | 256 | 0,0x10000 | 7..0,71..64 | 0,8,..56,128,136,..184 | 256 bits |
| 3bpp sprite | 256 | 0x20000,0x10000,0 | 7..0,71..64 | 0,8,..56,128,136,..184 | 256 bits |

MAME bit offset 0 means a byte's MSB. Its first plane is the highest pen bit. 2bpp palette base=0, 3bpp base=256; actual attribute selects only 16 colour groups, despite larger GFXDECODE allocation. Lookup is PROM[0x20+pen]&0f. Although 32 RGB entries are loaded, this driver only maps colours 0..15. RGB weights: red and green 33,71,151; blue 82,173. No stretching to the unused indirect bank.

## Interrupt, flip and samples

Control port 04 bit 0 gates one NMI per VBLANK, bit 1 is the game flip latch; bits 2/3 unknown. Reset sets NMI enable, flip and sample address to zero. No level IRQ is added. Source: [213–256](https://github.com/mamedev/mame/blob/5fdbebde74ce2cb4db89ae615860c51a1bbf1f38/src/mame/sanritsu/drmicro.cpp#L213-L256).

Sample command sets a 15-bit nibble address to (data&3f)<<9 and invokes the callback immediately. Callback reads sample[address/2]. Whole byte 70 stops and asserts decoder reset without incrementing (questioned by MAME). Otherwise emit high nibble at even addresses, low at odd, release decoder reset, increment modulo 8000. Callback continues while stopped. Sample timing is distinct from CPU NMI.

## Controls and DIP switches

All defined controls are active high. P1 bits 0..6 = up,right,down,left,action,coin,service. P2 bits 0..6 = up,right,down,left,action,start1,start2. Bit 7 unknown/zero. Both sticks are four-way. Full original input block: [287–350](https://github.com/mamedev/mame/blob/5fdbebde74ce2cb4db89ae615860c51a1bbf1f38/src/mame/sanritsu/drmicro.cpp#L287-L350).

The following options/defaults are generated from the pinned source; hardware SW locations are inverted (!). Defaults: DSW1=0x4d, DSW2=0x00.

| Bank | Mask | Name | Default | Encodings |
|---|---|---|---|---|
| 1 | 03 | Lives | 01 | 00=2; 01=3; 02=4; 03=5 |
| 1 | 04 | Demo Sounds | 04 | 00=Off; 04=On |
| 1 | 18 | Bonus Life | 08 | 00=30000 100000; 08=50000 150000; 10=70000 200000; 18=100000 300000 |
| 1 | 20 | Service Mode | 00 | 00=Off; 20=On |
| 1 | 40 | Cabinet | 40 | 40=Upright; 00=Cocktail |
| 1 | 80 | Flip Screen | 00 | 00=Off; 80=On |
| 2 | 07 | Coinage | 00 | 07=4C 1C; 06=3C 1C; 05=2C 1C; 00=1C 1C; 01=1C 2C; 02=1C 3C; 03=1C 4C; 04=1C 5C |
| 2 | 08 | Unused SW2:4 | 00 | 00=Off; 08=On |
| 2 | 10 | Unused SW2:5 | 00 | 00=Off; 10=On |
| 2 | 20 | Unused SW2:6 | 00 | 00=Off; 20=On |
| 2 | 40 | Unused SW2:7 | 00 | 00=Off; 40=On |
| 2 | 80 | Unused SW2:8 | 00 | 00=Off; 80=On |

## Uncertainties

MAME-modelled: functional maps, graphics, palette, sample sequence, flip, NMI gating and chip variants. Provisional: CPU clock questioned by MAME; no original raster totals/sync phases supplied; MAME's 2.5 ms VBLANK is explicitly inaccurate. Unresolved: control bits 2/3, watchdog/port 05, terminator 70, original analogue response and read-during-write behaviour. No independent PCB measurements are claimed. Those unknowns do not create invented circuitry.
