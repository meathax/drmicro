# Windows workstation setup

The workstation was inspected on 2026-09-06. Existing tools are reused; no global
PATH changes or duplicate toolchain installations are required.

| Tool | Installed location / version |
|---|---|
| Quartus Lite and Cyclone V device support | `D:/Q17/quartus`, 17.0.2 Build 602 |
| Python | `D:/vibes/fpga/toolchains/msys64/ucrt64/bin/python.exe`, 3.14.6 |
| Verilator | MSYS2 UCRT64 toolchain, 5.050, including runtime headers |
| Icarus / VVP | MSYS2 UCRT64 toolchain, 13.0 |
| GCC C++ | MSYS2 UCRT64 toolchain, 16.1.0 |
| Pillow and Tk | Available in the Python interpreter above |
| MAME | `D:/Arcade/AI/mameexe/mame.exe`, 0.289 |

`D:/Arcade/AI/mame289/mame.exe` reports 0.289 but does not include Dr. Micro.
Use the `mameexe` installation, whose ROM verification succeeds.

Machine-specific defaults live in ignored `.tools/local_env.json`:

```json
{
  "MAME": "D:/Arcade/AI/mameexe/mame.exe",
  "QUARTUS_ROOTDIR": "D:/Q17/quartus",
  "VERILATOR_ROOT": "D:/vibes/fpga/toolchains/msys64/ucrt64/share/verilator"
}
```

Explicit environment variables override these defaults. The driver passes the
resolved environment to its child processes. The existing user ROM archive is
copied into ignored `drmicro.zip` in the project root; all 16 manifest entries
match length, CRC32 and SHA-1. The three ignored Bank Panic reference RBFs were
restored from the pinned upstream commit and checked against the existing lock
file hashes. No dependency hashes were relaxed or regenerated.

Run `./tools/dev.ps1 test_all` to validate the simulation toolchain. The versions
above differ from the historical tool provenance in `docs/verification.md`;
new command reports establish their actual compatibility.

For a programming artifact, run these commands sequentially, stopping on failure:

```powershell
./tools/dev.ps1 quartus_map
./tools/dev.ps1 quartus_fit
./tools/dev.ps1 quartus_sta
./tools/dev.ps1 quartus_asm
```

Assembly requires a passing timing report with matching source hashes and records
the RBF size and SHA-256 in `reports/quartus_asm.json`. The artifact remains ignored
at `build/quartus/Arcade-DrMicro.rbf`. These commands never program hardware.
Constrained timing success does not close the known external I/O constraints or
the hardware-validation gates in `plan.md`.
