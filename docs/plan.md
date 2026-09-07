# Completion plan and current audit

## Current position

The project is a native synthesizable HDL implementation: TV80 executes the supplied Dr. Micro Z80 ROMs, and the tile, sprite, palette, PSG, ADPCM, input, loader and MiSTer wrapper paths are HDL. MAME 0.289 is an external behavioural reference only. `releases/Arcade-DrMicro_20260907.rbf` was built from the current source identity and plays on a DE10-Nano.

The active raster profile keeps reset and capture origin at y=240, and requests the NMI at x=316,y=239. It was selected from measured short-play comparisons. Relative to the former x=0,y=240 profile, it reduces frame-240 RGB differences from 75 to 24 and video-RAM differences from seven to two. In the same 300-frame run, frame 300 has exact RGB and video RAM. The more aggressive x=312,y=239 profile reaches the same frame-240 result but regresses to 100 RGB differences at frame 300, so it is rejected. The one-pixel sweep is complete: x=315 reaches 47 differing RGB pixels at frame 300, while x=317 matches x=316 with zero. Candidate evidence was recorded as `reports/comparison_nmi_sub*.json` (the `reports/` directory is generated and no longer tracked; rerun the scripts to regenerate).

The selected profile's fresh `play` evidence is strong but not a strict pass:

| Item | Measured result |
|---|---|
| Frames 1, 30, 60, 120 and 180 | Exact displayed RGB and video RAM |
| Frame 240 | 24 differing displayed RGB pixels; two differing video-RAM bytes; eight differing RAM bytes |
| Frame 300 | Exact displayed RGB and video RAM; eight differing RAM bytes remain |
| Ordered I/O writes | 1,154 / 1,154 exact |
| I/O reads | 883 / 883 exact |
| Per-chip sound commands | Exact: 71, 51, 168 and 0 writes |

This is evidence of close CPU/interrupt timing, but it does not prove board accuracy. The remaining RGB/RAM difference keeps the strict comparison gate at FAIL; its cause is now known (see step 2 below).

## Audit completed for this checkpoint

* `audit_source` passed for 533 Git-eligible paths. It found no ROM payload, generated asset, attribution or source-integrity problem.
* `lint_core` passed for the selected profile. The retained third-party synchronous/asynchronous reset warnings are documented; the core gate rejects the actionable warning classes.
* `test_unit` passed, including the 10-T RET, 11-T NMI, HALT/RETN, refresh, address-map, loader and memory-collision cases.
* `test_fixtures` passed, including both renderer orientations, 32,768 PSG events, independent JT5205 decoding and integrated audio.
* The selected-profile simulator was rebuilt and the 300-frame MAME `play` reference capture was regenerated before the comparison above.
* The selected-profile structural platform gate, HPS wrapper, rotation, video pipeline and project manifest checks pass. Quartus Analysis & Synthesis, fitting and four-corner timing were rerun on the current source identity; all pass.
* The one-pixel sweep around the selected NMI phase is complete: x=315 reaches 47 differing RGB pixels at frame 300, while x=317 matches x=316 with zero differing RGB pixels at frame 300. x=316 remains the production choice because it gives the best measured whole-window result and is the profile covered by the closure evidence.

## Remaining work, in execution order

1. **Re-established selected-profile build closure (done).** `check_platform`, `test_platform_hps` and `check_project` rerun clean. `quartus_map`/`fit`/`sta` rerun to match the current RTL/sys identity hash (`add1098d...`); all PASS. Two host-toolchain defects were found and fixed along the way (`docs/failures.md` 14-15): a `PATH`-order DLL mismatch that made `drmicro_sim.exe` fail to start and let one `test_all` run silently pass on a stale capture, and a GCC 16.1 inliner bug that crashed `test_platform_hps`. Neither was an RTL or protocol defect; both harnesses are now built `-static` / with `-fno-inline` and pass genuinely.
2. **Moving-game comparison root-caused, not yet strict (`docs/failures.md` 16).** A fresh PC/R trace at the NMI boundary proves CPU/interrupt execution is cycle-exact at frame 240 (and drifts by at most one PC sample, with R still exact, at two neighbouring frames). The 24-pixel/frame-240 mismatch is explained: the DUT's RAM/PPM snapshot is taken at vblank *start* (x=0,y=240); the game writes the two disputed tiles ~13 lines later, still inside the same vblank; MAME's `register_frame_done` snapshot evidently fires nearer vblank *end* and already reflects the write. Frame 300 (both sides converged) is exact. This is a comparison-harness sampling-instant mismatch, not a functional timing bug. Next step, not yet done: move the DUT's snapshot trigger in `sim/main.cpp` (and the equivalent point in `reference/capture.lua` if needed) from vblank start to vblank end, rerun `play`, and confirm the strict gate turns PASS for this case without moving any other frame's result. The NMI position sweep is complete, so any further timing change needs a whole-window justification.

   The 2,500-frame `cocktail` rerun on the fixed toolchain reinforces this: `all_io_writes` and `io_reads` are exact ordered matches for the entire run (10,230 and 7,568 events respectively, ordered signature comparison, not just counts) even through the death/restart transition, while periodic RGB/video-RAM/sprite-record differences recur near most 60-frame sample points, growing in extent as gameplay proceeds. Given the bus is proven bit-exact for the whole run, this pattern is consistent with the water/background animation updating on a period that keeps landing near the fixed 60-frame sampling instant, repeatedly hitting the same vblank-sampling-boundary artifact rather than indicating accumulating CPU/timing drift. `sprite_records_equal` turns false only at frames 2280/2340/2400 (near a death transition) — worth re-checking once the snapshot-instant fix lands, since it could be the same artifact reaching sprite RAM instead of tile RAM, or a distinct issue; not yet confirmed either way.
3. **Long trajectories rerun on the chosen profile (done 2026-09-07).** `attract`, `play`, `dips`, `service`, `reset`, `two` and `cocktail` were all rerun on the fixed toolchain, then `check_milestones` (all five outcome checks PASS), `test_cold_boots` (three identical boots) and `summarize_status`. `attract`, `dips` and `service` are strict passes. `reset` fails only the raw full-byte port-04 write at the soft-reset instant (unimplemented bits 2/3; RGB, reads, sound and known board effects exact). `play`, `two` and `cocktail` fail only on the vblank-sampling artifact of step 2 while every ordered I/O write and read matches for the full runs. The overall strict gate therefore stays FAIL until step 2's harness change lands; repeat this step after it.
4. **Resolve modelling unknowns with evidence.** The persistent RAM bytes (0xCF3C/0xCF3D/0xCFAA/0xCFAB) remain unexplained by the frame-240 finding above (they differ from frame 30 onward with no visible RGB effect; likely R-register-seeded state, but not confirmed) and still need PCB/board evidence, along with raster and blanking totals, CPU-clock and PSG-clock (MAME has used both 18.432/6 and 18.432/4 for the PSGs over time), port-04 control bits 2/3, port-05/watchdog behaviour, dual-port RAM collisions, MSM5205 stop/reset semantics, and analogue audio response. Do not invent hardware behaviour from a passing MAME comparison.
5. **Physical platform boundary (largely done).** RBF assembled after map/fit/sta on the current identity; loaded on a DE10-Nano through the MRA; ROM loading, portrait rotation, HDMI, controls and sustained gameplay confirmed by play. Still open: direct-video/analogue output check, and the inherited external I/O constraints (five inputs, 50 outputs partly or wholly unconstrained) which should be resolved from real board timing rather than masked.

## Completion criteria

The core is ready to call release-quality only when the selected RTL has fresh platform and Quartus evidence, the required scripted comparisons are strict passes or have explicitly approved hardware-backed exceptions, all external timing constraints are reviewed, and on-device DE10-Nano tests cover boot, gameplay, reset, controls, video and audio. As of 2026-09-07 every item except the strict moving-game comparison (explained, harness-side) and the external I/O constraint review is met; the core plays correctly on hardware.
