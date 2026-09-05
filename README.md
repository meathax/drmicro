# Dr. Micro for MiSTer — source and simulation development

This is a native synthesizable HDL implementation executing the original Z80 ROMs with TV80. It includes both tile layers, both sprite banks, PROM palette, three SN76496 adaptations, JT5205 ADPCM, controls, a validated byte loader and a real MiSTer emu wrapper. MAME is used only as an external reference. No software CPU, renderer or prerecorded game runs inside the core.

**This is not an RBF release or a hardware-verified core. Quartus 17.0.2 is available for explicit Analysis & Synthesis, fitting and timing checks.** Read [implementation status](docs/implementation_status.md) and the machine-readable [test report](reports/test_report.json) for actual completion gates and remaining differences.

From Windows PowerShell, run `./tools/dev.ps1 <command>`. On Linux/MSYS with Python 3, use `python3 tools/dev.py <command>` or `sh tools/dev.sh <command>`. The scripts locate project-local tools or use PATH; they never change global PATH. Optional Windows tool downloads are isolated in `.tools/`: `tools/bootstrap_tools.py` (Verilator/Icarus), `tools/bootstrap_cpp.py` (portable GCC), and `tools/bootstrap_mame.py` (official reference emulator). They download tools, never game ROMs. Tool versions and binary hashes are recorded in `reports/tool_provenance.json`.

```powershell
./tools/dev.ps1 fetch_deps
./tools/dev.ps1 check_deps
./tools/dev.ps1 check_roms
./tools/dev.ps1 pack_roms
./tools/dev.ps1 lint_core
./tools/dev.ps1 test_unit
./tools/dev.ps1 test_fixtures
./tools/dev.ps1 check_platform
./tools/dev.ps1 test_rotation
./tools/dev.ps1 test_platform_video
./tools/dev.ps1 test_platform_hps
./tools/dev.ps1 check_project
./tools/dev.ps1 build_sim --jobs 2
./tools/dev.ps1 run_smoke --frames 120
./tools/dev.ps1 run_reference --frames 120
./tools/dev.ps1 compare
./tools/dev.ps1 capture_assets
```

`test_all` implements the sequence above, one heavy operation at a time. PASS, FAIL and BLOCKED are distinct; missing assets/tools do not masquerade as success. Build parallelism is bounded (default two C++ translation units). No-ROM unit/fixture tests are independent of proprietary ROMs and MAME.

Longer scripted runs and reset/download stress:

```powershell
./tools/dev.ps1 run_smoke --frames 300 --script play
./tools/dev.ps1 run_reference --frames 300 --script play
./tools/dev.ps1 compare --script play
./tools/dev.ps1 capture_assets --script play
./tools/dev.ps1 run_smoke --frames 3600 --script two
./tools/dev.ps1 run_reference --frames 3600 --script two
./tools/dev.ps1 compare --script two
./tools/dev.ps1 run_smoke --script stress
```

`play`: coin at frames 180–182, start1 at 210–212, right/action at 240–329, up/action at 330–399. `two`: two coins then start2. `dips`: five lives, flip and one coin/two credits with the play inputs; `service`: service DIP; `cocktail`: two-player inputs with cabinet DIP; `reset`: soft reset at frame 240 followed by a fresh boot. These are input schedules, not assumed gameplay milestones. The runner saves native 256×224 PPM images, raw pen indices, RAM snapshots, CPU fetch/I/O logs and five-source 48 kHz audio. `capture_assets` makes WAVs and independent graphics contact sheets. `compare` creates portrait PNGs. Optional `python tools/view_capture.py reports/captures/play` opens a Tk/Pillow frame browser; the headless runner does not require a GUI.

Place only your own `drmicro.zip` in this directory or under `roms/`, `game/`, `games/`; extracted physical files in those directories also work. All 16 files must match filename, length, CRC32 and SHA-1 from `reference/rom_manifest.json`. The canonical packed payload is 107,040 populated bytes, with no padding. Generated ROM assets and captures are ignored by Git. See [ROM layout](docs/rom_layout.md), [hardware specification](docs/hardware_spec.md), [timing/memory](docs/timing_memory.md), [audio](docs/audio.md), [inputs](docs/inputs.md), [platform boundary](docs/platform.md), and [diagnosed failures](docs/failures.md).

Source lists are explicit: `sim/core.f` for the DUT, `sim/platform.f` for wrapper elaboration, `files.qip` plus pinned platform QIPs for a future hardware build. `screen_rotate` is defined once inside `sys/arcade_video.v`. The QPF/QSF/SDC files have structural checks plus explicit Quartus stage reports. On-chip logical memory is estimated at 992,000 bits; this is not a fitter result.

Third-party source is pinned in `third_party.lock.json`, with complete upstream notices and maintained patches. New contributions use GPL-3.0-or-later; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for file-specific donor licensing. The private GitHub repository is connected as origin and committed source checkpoints are pushed.

Additional outcome coverage (run each reference/compare with the same script and frame count):

```powershell
./tools/dev.ps1 run_smoke --frames 300 --script dips
./tools/dev.ps1 run_reference --frames 300 --script dips
./tools/dev.ps1 compare --script dips
./tools/dev.ps1 run_smoke --frames 120 --script service
./tools/dev.ps1 run_reference --frames 120 --script service
./tools/dev.ps1 compare --script service
./tools/dev.ps1 run_smoke --frames 360 --script reset
./tools/dev.ps1 run_reference --frames 360 --script reset
./tools/dev.ps1 compare --script reset
./tools/dev.ps1 run_smoke --frames 2500 --script cocktail
./tools/dev.ps1 run_reference --frames 2500 --script cocktail
./tools/dev.ps1 compare --script cocktail
./tools/dev.ps1 check_milestones
./tools/dev.ps1 test_cold_boots
./tools/dev.ps1 audit_source
```

`check_milestones` also requires the 300-frame play and 3,600-frame two-player captures. Strict comparisons deliberately return a failure for unresolved pixels/order or raw control-byte differences. Read their per-check results; a passing smoke/outcome check does not override a strict failure. Source hashes for every HDL input, macro file, read-only observation configuration and C++ runner are recorded with new captures; subsequent builds write a binary manifest checked before execution.

`./tools/dev.ps1 summarize_status` writes the overall machine-readable gate, including all scripted comparisons. It currently returns FAIL for unresolved strict moving-game equivalence; this is intentional and separate from a passing default test_all.

Quartus validation policy: run Analysis & Synthesis after substantial RTL changes; run fitting and timing analysis after large RTL changes. The local installation is `C:/intelFPGA_lite/17.0/quartus`; override with `QUARTUS_ROOTDIR` elsewhere. These stages are sequential and check that prior-stage source hashes are current:

```powershell
./tools/dev.ps1 quartus_map
./tools/dev.ps1 quartus_fit
./tools/dev.ps1 quartus_sta
```

Reports are retained under `reports/quartus_*`; build databases and detailed reports are ignored under `db/`, `incremental_db/` and `build/quartus/`. These commands do not assemble an RBF or program hardware. The simulation-only `test_all` does not invoke Quartus implicitly.
