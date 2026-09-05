# Implementation status

This is a native HDL core executing the audited original ROMs in Verilator, with MAME 0.289 as the independent reference and Icarus for four-state tests. It is source/simulation development, not an RBF release. The user has now authorized Quartus Analysis & Synthesis and fitting. Explicit stage results are recorded in reports/quartus_*.json; hardware operation remains untested.

## Executed evidence

| Check | Status | Evidence and limits |
|---|---|---|
| Dependency / ROM audit | PASS | 323 pinned source/materialization/patch hashes; all 16 ROM files match size, CRC32 and SHA-1. Generated game assets remain ignored. |
| Core lint / four-state tests | PASS | Bus read retention, full 65,536-address decode, memory collisions/clear, loader recovery, controls; no waived board structural/width defects. |
| CPU timing / refresh | PASS | RET 10 T states, NMI 11, HALT wake/RETN, LD A,R value/flags, seven-bit refresh wrap; branches, block copies, indexed operations, stack and conditional returns. Original donor preserved with patches. |
| Independent renderer | PASS | 57,344 raw pens and RGB pixels in each flip orientation, adversarial synthetic tiles/sprites, no X or missed scanline deadline. |
| Independent audio | PASS | 32,768 PSG vectors, 256 standalone decoder samples, 5,143 integrated samples across all 64 sample pages, restart/stop and mixer checks. Digital behaviour only. |
| Real-ROM two-player run | PASS smoke/outcomes | 3,600 frames, 22,792,458 opcode fetches, 3,510,032 RAM writes, 15,060 I/O writes and 3,587 NMI events. Captures show two-player selection, death and player-two restart. |
| Real-ROM sound commands | PASS | Over those 3,600 frames, exact per-chip sequences: 676/34/3,584 PSG writes and one ADPCM command 0x21. Cross-port timing is a separate check. |
| Short gameplay / DIP I/O | PASS | Both 300-frame scripts match all 1,154 writes and 883 reads. DIP run confirms five lives, one remaining credit after one coin/start with 1C/2C, and game flip. |
| Cocktail player-two flip | PASS outcomes | 2,500 frames with cabinet DIP; state transition and flip at frame 2460 match the reference. |
| Service-mode strict comparison | PASS | All four captures, 234 writes and 190 reads match the reference over 120 frames. |
| Full boot after game reset | PASS outcomes | Reset at frame 240 returns to the title at 360. All eight captures, reads and known board effects match. Raw unused control bits differ from MAME soft reset; strict report preserves this. |
| Three full cold boots | PASS | Three independent 120-frame boots have identical native RGB, raw pens, complete RAM snapshots and execution counters. |
| Reset / download stress | PASS | Four cold releases, six re-downloads, three game resets, three rejected short loads, three separate DIP-index sessions. See separate full-boot checks for completed boot coverage. |
| Actual HPS wrapper | PASS | ROM download/rejection, DIP updates without reset, both joysticks, PS/2 make/break, aspect and OSD reset followed by CPU execution. Real emu and hps_io; physical HPS bridge excluded. |
| Actual video pipeline / rotation | PASS | Native coordinate colours, gamma, scandoubler and HQ2x output counts; CCW DDR address/byte-lane mapping and bypass. Behavioural always-ready DDR boundary. |
| Platform warning gate | PASS | 93 exact-message, source-hash-bound donor waivers with explanations. New structural/implicit/undriven warnings fail. Logs retain all warnings. |
| Quartus Analysis & Synthesis | PASS | Quartus 17.0.2, full sys_top, zero errors and 76 reviewed warnings. Clock-switch legality is retained in a source patch. |
| Quartus fitting | PASS | 10,085/41,910 ALMs (24%), 14,917 registers, 202/553 RAM blocks (37%), 1,507,777 memory bits (27%), 34/112 DSPs (30%); zero fitter errors. |
| TimeQuest constrained timing | PASS | Four corners: minimum setup +0.217 ns, hold +0.080 ns, recovery +3.943 ns, removal +0.469 ns, pulse width +1.122 ns. Zero unconstrained clocks. |
| External I/O timing closure | NOT_RUN | Inherited constraints leave 5 inputs and 50 outputs partly/unconstrained, including HDMI. No fabricated pin budgets or blanket false paths were added. |
| Future project / MRA | PASS | Explicit source closure, simulation/FPGA TV80_REFRESH agreement, recursive QIP paths and independent byte-for-byte reconstruction of the 107,040-byte MRA payload. Not Quartus validation. |
| Strict moving-game comparison | FAIL | After reset-aligning the fractional CPU/raster enables, short play differs by 75 and 28 pixels at frames 240/300 while all 1,154 writes and 883 reads remain exact. Long two-player evidence predates that timing refinement: six exact captures out of 62, up to 993 differing pixels; first full-I/O ordering divergence occurs around death, frame 2233/2234. Per-chip sound commands still match. |
| Physical platform / hardware | NOT_RUN | DE10-Nano validation remains future work. No RBF exists. |

`reports/verification_summary.json` is the overall strict gate and stays FAIL while moving-game equivalence is unresolved. `reports/test_report.json` contains the latest command results; `reports/test_history.jsonl` preserves later invocations. Script-specific comparisons retain strict failures. Ignored capture result files include ROM/source/runner/binary hashes and build configuration. `reports/milestones.json` records reference-correlated outcomes separately from strict trajectory equivalence.

## Remaining issues

**Implementation/comparison:** Strict moving-game equivalence remains unresolved. Resetting the fractional CPU, audio and raster enables while the board is held in ROM/RAM reset improved the 240-frame water difference from 115 to 75 pixels, but water-animation RAM differences and a later death-transition timing difference remain visible. Independent rendering of each side's RAM distinguishes game-state differences from live raster/snapshot timing. All 62 reference snapshots match the independent renderer; the DUT agrees with its own captured RAM on 34 frames, with up to 99 pixels/pens differing due to the live/snapshot boundary. Those observations do not waive the cross-reference failures. The game uses Z80 R for randomness; that observation alone does not prove every difference harmless. A candidate that mapped MAME's explicitly provisional 2,500 us vblank to NMI line 218 made the frame-240 comparison 137 pixels and changed ordered I/O at frame 185, so the maintained line-240 profile remains selected. Do not call the core perfect or cycle-exact.

**Missing assets/tools:** None block current simulation/reference checks. The user ROMs and local Verilator, Icarus, GCC and MAME are available. The optional GUI capture viewer is not part of the verified path.

**Uncertain hardware facts:** CPU rate is questioned in MAME, native raster/blanking totals are provisional, control bits 2/3 are unknown, and original analogue audio and read-during-write behaviour lack PCB measurements. The JT5205 donor retains a one-sample pipeline and -2 reset baseline; no sample-exact MAME or analogue claim is made.

**Quartus/on-device:** Analysis & Synthesis, fitting and four-corner constrained timing pass. External I/O timing coverage is incomplete. Physical HPS/DDR, HDMI/direct-video, orientation, controls and audio still require DE10-Nano testing. No RBF generation or programming has been performed.

The private GitHub repository is `meathax/drmicro`; origin is configured and the committed source checkpoints are pushed.
