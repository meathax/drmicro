# Completion plan and current audit

## Current position

The project is a native synthesizable HDL implementation: TV80 executes the supplied Dr. Micro Z80 ROMs, and the tile, sprite, palette, PSG, ADPCM, input, loader and MiSTer wrapper paths are HDL. MAME 0.289 is an external behavioural reference only. No RBF has been generated and no DE10-Nano has been programmed.

The active raster profile keeps reset and capture origin at y=240, and requests the NMI at x=316,y=239. It was selected from measured short-play comparisons. Relative to the former x=0,y=240 profile, it reduces frame-240 RGB differences from 75 to 24 and video-RAM differences from seven to two. In the same 300-frame run, frame 300 has exact RGB and video RAM. The more aggressive x=312,y=239 profile reaches the same frame-240 result but regresses to 100 RGB differences at frame 300, so it is rejected. Candidate evidence is retained in `reports/comparison_nmi_sub4.json`, `reports/comparison_nmi_sub8.json`, and `reports/comparison_nmi_sub.json`.

The selected profile's fresh `play` evidence is strong but not a strict pass:

| Item | Measured result |
|---|---|
| Frames 1, 30, 60, 120 and 180 | Exact displayed RGB and video RAM |
| Frame 240 | 24 differing displayed RGB pixels; two differing video-RAM bytes; eight differing RAM bytes |
| Frame 300 | Exact displayed RGB and video RAM; eight differing RAM bytes remain |
| Ordered I/O writes | 1,154 / 1,154 exact |
| I/O reads | 883 / 883 exact |
| Per-chip sound commands | Exact: 71, 51, 168 and 0 writes |

This is evidence of close CPU/interrupt timing, but it does not prove board accuracy. The remaining RGB/RAM difference keeps the strict comparison gate at FAIL.

## Audit completed for this checkpoint

* `audit_source` passed for 530 Git-eligible paths. It found no ROM payload, generated asset, attribution or source-integrity problem.
* `lint_core` passed for the selected profile. The retained third-party synchronous/asynchronous reset warnings are documented; the core gate rejects the actionable warning classes.
* `test_unit` passed, including the 10-T RET, 11-T NMI, HALT/RETN, refresh, address-map, loader and memory-collision cases.
* `test_fixtures` passed, including both renderer orientations, 32,768 PSG events, independent JT5205 decoding and integrated audio.
* The selected-profile simulator was rebuilt and the 300-frame MAME `play` reference capture was regenerated before the comparison above.
* `test_platform_video` completed successfully for the selected profile before the stop request took effect. The structural wrapper check, HPS wrapper test and project check remain evidence from the earlier profile and need rerunning. Quartus evidence also predates the selected default.

## Remaining work, in execution order

1. **Re-establish selected-profile build closure.** Run `check_platform`, `test_platform_hps` and `check_project`. Run `quartus_map` because the RTL default/source digest changed. Record the new source hash with the report. This parameter-only change is not a large RTL restructuring, so repeat fitting and TimeQuest only if Analysis & Synthesis changes the netlist/resources or a later larger change requires them.
2. **Make the short moving-game comparison strict.** Preserve the immutable MAME capture while sweeping the remaining one-pixel NMI positions around x=316. Retain every candidate report. For the first diverging frame, compare RAM addresses, I/O time stamps and PC/R NMI-boundary traces; use MAME debugger traces only as diagnostics, never as a strict capture source. Accept a timing profile only when it improves the whole measured window, not a single checkpoint.
3. **Re-run long trajectories on the chosen profile.** Repeat `two`, `cocktail`, `dips`, `service` and `reset`, then `check_milestones` and `summarize_status`. The currently recorded death-transition ordering divergence and long-run capture counts predate this NMI choice, so they are not final evidence for the selected profile.
4. **Resolve modelling unknowns with evidence.** Investigate the persistent RAM bytes and frame-240 water writes first. Then obtain PCB/board evidence for raster and blanking totals, CPU-clock phase, port-04 control bits 2/3, port-05/watchdog behaviour, dual-port RAM collisions, MSM5205 stop/reset semantics, and analogue audio response. Do not invent hardware behaviour from a passing MAME comparison.
5. **Close the physical platform boundary.** After simulation and Quartus closure, generate a reviewable programming artifact, then test ROM loading, inputs/DIPs, reset, portrait rotation, HDMI/direct video, audio, HPS/DDR and sustained gameplay on a DE10-Nano. External I/O constraints currently leave five inputs and 50 outputs partly or wholly unconstrained; resolve those from real board timing rather than masking them.

## Completion criteria

The core is ready to call release-quality only when the selected RTL has fresh platform and Quartus evidence, the required scripted comparisons are strict passes or have explicitly approved hardware-backed exceptions, all external timing constraints are reviewed, and on-device DE10-Nano tests cover boot, gameplay, reset, controls, video and audio. Until then it remains a simulation-validated native core with known moving-game and physical-hardware gaps.
