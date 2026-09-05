# Canonical ROM payload

Generated from the pinned MAME physical ROM definitions. No header, padding or trailer. Bytes follow region/file order. CPU allocation is 64 KiB but only its populated 48 KiB is packed. The total is 107040 bytes. MRA, packer, loader constants and simulation use `reference/rom_manifest.json`.

| Region | Packed offset | Populated | MAME allocation |
|---|---:|---:|---:|
| maincpu | 0x00000 | 0xc000 | 0x10000 |
| gfx1 | 0x0c000 | 0x4000 | 0x4000 |
| gfx2 | 0x10000 | 0x6000 | 0x6000 |
| adpcm | 0x16000 | 0x4000 | 0x4000 |
| proms | 0x1a000 | 0x220 | 0x220 |

`tools/roms.py` checks filename, length, CRC32 and SHA-1 before packing. The loader enforces one sequential byte session at index 0 with exact length, no repeated/missing addresses. Host validation checks content; the hardware loader checks transport completeness, not cryptographic authenticity. Index 254 DIP sessions leave loaded ROMs valid. Game reset clears volatile RAM sequentially and preserves ROM bytes/validity; cold reset invalidates the loader. Invalid/short/interrupted downloads hold the CPU reset.
