# Dr. Micro for MiSTer

An FPGA recreation of Sanritsu's 1983 *Dr. Micro* arcade hardware for the MiSTer DE10-Nano. The board is implemented natively in synthesizable HDL: the original Z80 program runs on a cycle-corrected TV80, and both tile layers, both sprite banks, the PROM palette, the three SN76496 PSGs and the MSM5205 sample channel are all real logic. MAME is used only as an external behavioural reference; no software CPU, renderer or recording runs inside the core.

| | |
| --- | --- |
| **Target** | MiSTer DE10-Nano. No SDRAM module required; the whole board fits in on-chip block RAM |
| **Original hardware** | Sanritsu Z80 board, 18.432 MHz master clock, three SN76496, one MSM5205 |
| **Video** | Vertical (portrait) 256×224 raster, 60 Hz, presented rotated through MiSTer's framebuffer path with the usual scaler options |
| **Audio** | Mono: three SN76496 PSGs plus MSM5205 ADPCM samples |
| **Core file** | `Arcade-DrMicro` |

## Supported games

| MAME set | Title | Year | Manufacturer | MRA |
| --- | --- | --- | --- | --- |
| `drmicro` | Dr. Micro | 1983 | Sanritsu | `Dr. Micro.mra` |

## Features in the OSD

| Control or option | Default | Purpose |
| --- | --- | --- |
| Action | `A` | Player action button |
| Start 1 / Start 2 | `Start` / `Select` | Cabinet start buttons (either pad can press Start 2) |
| Coin | `R` | Cabinet coin input |
| Service | `L` | Cabinet service input |
| Orientation | Vertical | Rotate for a normal landscape display, or Native for a rotated monitor / direct video |
| Scandoubler Fx | None | HQ2x or CRT scanline shading |
| Aspect ratio | Original | Original, Full Screen or the two custom ARC ratios |
| DIP switches | 3 lives, 1C/1C, upright | Full DSW1 / DSW2 page from the MRA: lives, demo sounds, bonus life, service mode, cabinet, flip screen, coinage |
| Reset | — | Board reset; ROM stays loaded |

Keyboard: P1 arrows and left Ctrl, P2 R/F/T/D and left Alt, `5` coin, `1` / `2` start, `F3` service. Opposite joystick directions cancel and vertical wins a simultaneous diagonal, matching the game's 4-way stick.

## PCB accuracy

This section separates what is backed by direct evidence from what is inferred from MAME. MAME is a good functional reference for this board but its own driver marks the CPU clock and the vertical blanking interval as unverified, so it is not treated as PCB proof.

| Area | Status | Evidence |
| --- | --- | --- |
| Z80 instruction timing | **KNOWN** | The TV80 donor was corrected to the documented Z80 T-state counts for unconditional RET (10 T), NMI entry (11 T), HALT/RETN and the seven-bit refresh register with LD A,R flags. Each fix has a standalone timing testbench that fails on the original file and passes on the derived one. |
| CPU / interrupt phase against the reference | **KNOWN** | A PC and refresh-register trace taken at every frame's NMI request agrees with MAME to the instruction across a 300-frame gameplay run; every ordered I/O write and read (15,060 and 11,976 events over a 3,600-frame two-player run) matches exactly. |
| Memory map, video RAM layout, tile and sprite formats, palette PROM decode | **INFERRED** | Derived from the ROM/PROM contents and the pinned MAME driver; confirmed by the game running correctly on hardware and by pixel-exact captures against MAME on the attract, service, DIP and reset scripts. |
| SN76496 register model, noise LFSR, attenuation curve | **INFERRED** | Follows MAME's SN76496 variant (17-bit LFSR, taps 0x04/0x08, 2 dB steps) and is checked against an independent state machine over 32,768 events. |
| MSM5205 decode and sample sequencer | **INFERRED** | JT5205 decoder with MAME's 15-bit sample address, 6 kHz (S64) rate and `0x70` end marker; checked against an independent integer decoder. |
| Raster totals, blanking length, refresh rate | **HYPOTHESIS** | MAME uses 60 Hz with an explicitly "not accurate" 2.5 ms vblank. The core uses a 320×256 raster at 60.00 Hz derived from the 50 MHz system clock. A real board driven from the 18.432 MHz crystal would more plausibly run 6.144 MHz pixels, 384 pixels per line and 264 lines (about 60.6 Hz); this has not been measured. |
| CPU and PSG clock | **HYPOTHESIS** | 18.432 MHz / 6 = 3.072 MHz per MAME, which marks it with a question mark. Older MAME versions clocked the PSGs at 18.432 MHz / 4 instead, which would raise music pitch by a factor of 1.5. Needs a PCB audio recording to settle. |
| Port 05 read value, control-port bits 2 and 3, analogue mixing and filtering | **HYPOTHESIS** | Unknown; the core follows MAME (port 05 reads 0, bits 2/3 ignored, equal PSG gains). No gameplay effect has been found. |

The one remaining strict-comparison difference against MAME (a handful of background tiles in one frame of a moving-game capture) was traced to the two test harnesses sampling "end of frame" at different points inside vertical blanking, not to a CPU or video timing error. The core's live-rendered picture is unaffected; the two sides agree again on the following captured frame.

## Hardware emulated

| Original device or function | FPGA path | Evidence status |
| --- | --- | --- |
| Z80 CPU at 3.072 MHz | `rtl/derived/tv80_core.v`, `rtl/derived/tv80_mcode.v` (TV80 with exact patches in `patches/`) | **KNOWN** timing corrections, **INFERRED** clock |
| Address decoder, bus hold and I/O ports | `rtl/drmicro_bus.sv`, `rtl/drmicro_core.sv` | **INFERRED** from the MAME map |
| Program ROM, work RAM, video RAM, graphics ROMs, PROMs | `rtl/drmicro_memory.sv` (all block RAM) | **INFERRED** |
| Two 32×32 tile layers and two 8-sprite banks, line-buffered scanline renderer | `rtl/drmicro_video.sv` | **INFERRED** |
| Colour PROM lookup and resistor-ladder DAC weights | `rtl/drmicro_memory.sv`, `rtl/drmicro_video.sv` | **INFERRED** (33/71/151 and 82/173 weights as in MAME) |
| Three SN76496 PSGs | `rtl/sn76496_jt89.sv` (JT89 register structure, MAME SN76496 variant behaviour) | **INFERRED** |
| MSM5205 ADPCM and its ROM sequencer | `rtl/vendor/jt5205`, `rtl/derived/jt5205_adpcm.v`, `rtl/drmicro_adpcm_ctrl.sv` | **INFERRED** |
| NMI gate, flip latch, sample trigger | `rtl/drmicro_core.sv`, `rtl/drmicro_sound.sv` | **INFERRED** |
| Controls, DIP switches, ROM loader | `rtl/drmicro_inputs.sv`, `rtl/drmicro_rom_loader.sv` | Platform integration |

MiSTer ROM loading, HPS I/O, OSD, rotation and video output (`sys/`, `Arcade-DrMicro.sv`) are platform integration, not original Sanritsu hardware.

## ROMs and MRAs

ROM images are not included. Use a legally obtained `drmicro.zip` matching the MAME `drmicro` set (16 files, 107,040 bytes of payload). The MRA supplies the ROM ordering and the DIP switch page.

Place the archive in MiSTer's MAME ROM directory:

```text
/media/fat/games/mame/drmicro.zip
```

## How to install

Copy the RBF and MRA to the MiSTer Arcade directories:

```text
/media/fat/_Arcade/cores/Arcade-DrMicro_20260907.rbf
/media/fat/_Arcade/Dr. Micro.mra
```

Then launch **Dr. Micro** from the Arcade menu. The published files are:

| File | Repository location |
| --- | --- |
| Core RBF | `releases/Arcade-DrMicro_20260907.rbf` |
| MRA | `releases/Dr. Micro.mra` |

## Release

The current committed release is `Arcade-DrMicro_20260907.rbf`, built with Quartus Prime 17.0.2 for the Cyclone V `5CSEBA6U23I7`. It has been booted and played on a DE10-Nano.

```text
SHA-256: 7CFFB32231A88F2E88AA50CFD7EC5FC440C1F4B1DDA660457115ADA81B1B3B46
```

Resource use: 10,085 of 41,910 ALMs, 202 of 553 M10K blocks, 34 DSP blocks. Timing closes at all four operating-condition corners with no unconstrained clocks. Only the newest accepted dated RBF is kept in `releases/`.

## Building from source

The Quartus project is `Arcade-DrMicro.qpf`, with `Arcade-DrMicro.qsf`, `Arcade-DrMicro.sdc` and `files.qip` supplying the settings, constraints and source manifest. The supported toolchain is Quartus Prime 17.0.2 Build 602 for the DE10-Nano Cyclone V `5CSEBA6U23I7`.

Open the project in Quartus and run Analysis & Synthesis, Fitter, TimeQuest and Assembler in that order, or from a shell:

```bash
quartus_map Arcade-DrMicro -c Arcade-DrMicro
```

```bash
quartus_fit Arcade-DrMicro -c Arcade-DrMicro
```

```bash
quartus_sta Arcade-DrMicro -c Arcade-DrMicro
```

```bash
quartus_asm Arcade-DrMicro -c Arcade-DrMicro
```

The RBF is written to `build/quartus/Arcade-DrMicro.rbf`. Generated databases, fitter output, simulation results and ROM images are not tracked.

## Verification

The core was developed against a differential test suite that is maintained outside this repository: four-state unit tests for the corrected Z80 timing, the loader, the bus and the memory collisions; independent reference models for the renderer, the SN76496 and the MSM5205 decoder, compared over randomised stimulus; elaboration of the real MiSTer `emu` wrapper with `hps_io` and the full video pipeline; and frame-by-frame differential runs of the whole board on the real ROMs across attract, gameplay, two-player, DIP, service, cocktail and reset scripts.

Headline results: every ordered I/O write and read matches the reference over a 3,600-frame two-player run (15,060 writes and 11,976 reads); three independent cold boots produce bit-identical pixels, RAM and instruction counts; and the attract, DIP and service scripts are pixel-exact. Remaining differences and their causes are summarised in the PCB accuracy table above.

## Credits

- [Guy Hutchison's TV80](https://github.com/hutch31/tv80) (based on Daniel Wallner's T80), for the Z80 core.
- [JT89 and JT5205](https://github.com/jotego) by Jose Tejada, for the SN76489-family PSG structure and the MSM5205 decoder.
- [MiSTer-devel/Template_MiSTer](https://github.com/MiSTer-devel/Template_MiSTer) by Sorgelig, for the platform framework.
- [MAME](https://www.mamedev.org/), and Uki's `drmicro` driver in particular, for reference behaviour, ROM naming and ROM mappings.
- Sanritsu and the original rights holders. Game ROMs are not distributed with this project.

## License

Project-specific source is distributed under the [GNU General Public License, version 3 or later](LICENSE). Vendored TV80, JT89, JT5205 and MiSTer framework components retain their upstream copyright and licence notices; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and `third_party.lock.json` for the pinned provenance of every third-party file and patch.
