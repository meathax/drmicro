# Validation policy

The user has installed Quartus at `C:/intelFPGA_lite/17.0/quartus` and requires
Analysis & Synthesis for substantial RTL changes. Large RTL changes also require
fitting; run timing analysis after fitting and report violations explicitly.

Use `./tools/dev.ps1 quartus_map`, then `quartus_fit` and `quartus_sta` as appropriate.
The same commands work through `python tools/dev.py` with `QUARTUS_ROOTDIR` set on
other hosts. Run affected simulation tests as well. Keep Quartus stages sequential
and retain source hashes and reports. A successful fit is not a hardware test.

Keep user ROMs, captures, generated programming files and tool binaries out of Git.
Do not push source or program hardware without user authorization.
