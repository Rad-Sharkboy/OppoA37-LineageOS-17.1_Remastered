# V2.1 ROM download

[**Download Lineage_17.1_REMASTERED_V2.1.zip (559 MB)**](https://github.com/Rad-Sharkboy/OppoA37-LineageOS-17.1_Remastered/raw/refs/heads/v2.1-download/downloads/V2.1/Lineage_17.1_REMASTERED_V2.1.zip)

For Oppo A37 / A37f / A37fw. This complete flashable ZIP includes E001–E006, integrated power profiles and the rebuilt kernel. CPU/GPU overclocks and the 65 Hz display configuration are retained.

1. Download the ZIP using the link above. It must be **558,701,081 bytes**; a small text file is an LFS pointer, not the ROM. Use the ZIP link rather than GitHub's repository source archive.
2. In TWRP, back up Boot, System and Data. Keep the working V2 ZIP available.
3. Flash V2.1 over V2 **without wiping or formatting Data**, then reboot. No separate kernel flash or ADB tuning commands are needed.

Reinstall Magisk afterward if you want root; system add-ons installed outside V2 may also need reinstalling. Tuning works without root. Like V2, this ZIP is unsigned; leave TWRP ZIP signature verification off.

[Installation, quick check and rollback](READ-ME-FIRST.txt) · [SHA256SUMS](SHA256SUMS) · [Build manifest](build-manifest.json)

SHA-256: `65cc34a16b2808475e0b76096ed157852ed7252bda13e00b996ee930853c1b77`
