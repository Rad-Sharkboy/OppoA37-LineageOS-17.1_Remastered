# ⚡ LineageOS-17.1-OppoA37-f-fw-Remastered

> **A storage and RAM debloated, bare-metal optimized custom build of LineageOS 17.1 (Android 10) tailored specifically to get better battery life and somewhat refined UI responsiveness for the Oppo A37, A37f, and A37fw.**

⚠️ **CRITICAL DEVICE WARNING:** 
**THIS ROM IS STRICTLY FOR THE OPPO A37 / A37f / A37fw. DO NOT FLASH THIS ON OTHER DEVICES.**

### Disclaimer & Credits:

**I take ZERO credit for the original LineageOS base, the OS framework, or the custom kernel.** 
The heavy lifting and critical development for this device were done by the incredibly talented original developers. All respect and credit go to:

* **The LineageOS Team:** For the phenomenal base source code.
* **Megh Rana:** For porting the Android 10 device tree to this specific series of devices ([GitHub](https://github.com/Megh-Rana)).
* **noverisp3:** For the custom overclocked kernel ([GitHub](https://github.com/noverisp3)). *(I simply compiled this kernel directly into the flashable `boot.img` so you don't have to flash it separately).*

I simply took their amazing foundation, cleaned up the file system, optimized the UI responsiveness, and tailored it for better battery life and daily usage. I am uploading it here to help anyone else out there who wants a cleaner, smoother Android 10 experience on this hardware.

---

## ⚡ Features & Optimizations

This ROM is a **64-bit** build that has been heavily debloated and tweaked for the Snapdragon 410.

### Storage & RAM Savings
* **Reduced Zip Size:** Cut down the installation zip size by around **100MB**.
* **Reduced RAM Usage:** Saved around **100MB of RAM** by disabling background caching for heavy apps like the Browser, executing deep filesystem cleanups, and deleting redundant `.oat` files.
* **Heavy Debloat:** Removed useless LineageOS system APKs that most people never use.
* **Media & Customization Purge:** Removed redundant fonts, extra languages, system wallpapers, and heavy ringtones/notification sounds. (It's much easier to just download a picture from your gallery to set as a wallpaper or download your own ringtones). *Note: Customization options are reduced, but you can always restore fonts via root packages.*

### App & UI Upgrades
* **GCam Go & Camera Overhaul:** Ripped out the stock AOSP camera and replaced it with a hardware-optimized GCam Go port. 
  * Ported front camera `lib_chromatix` files from the OnePlus One (shared sensor) to vastly improve saturation, sharpness, and temporal denoising. 
  * Reverse-engineered GCam Go's HDR pipeline to merge up to 6 frames for massive dynamic range/noise improvements.
* **Google Dialer:** Replaced the stock dialer with the Google Dialer for its advanced features. 
  *(⚠️ **Warning:** If you open it and see a "Device Unsupported" popup, just ignore it. It happens because the ROM doesn't have Google Mobile Services pre-installed. The dialer will still work perfectly for calls, and if you flash a GApps package, the popup goes away).*
* **Updated Boot & Charging UI:** Merged the latest LineageOS 23.2 boot animation and replaced the legacy offline charging animation with a modernized UI for clearer battery percentage visibility.
* **Updated Core Apps:** Updated all included APKs to their latest supported versions, especially the Android System WebView, so modern websites load correctly.
* **Lighter Keyboard:** Replaced the heavy default AOSP keyboard with a much lighter, faster version.
* **Audio Boost:** Natively boosted the system sound volume.
* **Classic Hardware Keys:** Restored the old, highly requested menu button behavior (**1 Press** = Recents Panel, **Long Press** = Split-screen multitasking).
* **Security Patch Spoofed:** Spoofed the Android security patch date to the latest available date. *Note: This is purely to bypass artificial requirements and trick modern apps into installing. It does not actually contain upstream security fixes.*

### Under-The-Hood Tweaks
* **3-in-1 Flash:** The `fix_baseband` patch (for cellular/RIL) and the custom kernel are already baked directly into this ROM. One flash gets you everything.
* **Hardware Video Encoding Uncapped:** Modified `media_profiles_V1_0.xml` and `fstab` to lift hardware encoding restrictions for superior image and video quality (media files will be slightly larger).
* **USB & ADB Fixes:** Fixed the MTP/Charging initialization bug (internal storage now mounts to PC perfectly) and restored the standard ADB debugging toggle for users in Developer Options.
* **Lower CPU Idle:** The CPU can now idle at its absolute minimum of **200MHz** (instead of being capped at 400MHz) to save standby power.
* **Battery Accuracy:** Fixed the internal battery profile to match the exact physical capacity of the A37's battery for much better battery level reporting.
* **Hardware Brightness Fix:** Calibrated internal framework values to fix the auto-brightness and brightness slider so it perfectly matches the phone's physical LCD limits.
* **Native System Optimizations:** Tweaked default system settings to disable heavy wakelocks and battery-draining features right out of the box.
* **Prop Tweaks:** Added multiple `build.prop` and `default.prop` tweaks to improve UI rendering, sleep policies, and overall responsiveness.
* **Network & Memory:** Optimized Wi-Fi and cellular connections, alongside improvements to Qualcomm memory management and CPU governor algorithms.
* **Telemetry Disabled:** Stripped Google telemetry, analytics tracking, and redundant system loggers from apps to save background CPU cycles and enhance privacy.

---

## Development branch power tuning

* **Shorter GPU idle delay:** Reduced the wait before the GPU attempts a low-power state from **500 ms to 80 ms**. This can reduce battery use between short rendering bursts while retaining GPU clock limits and the 65 Hz display.
* **Lower initial CPU boost:** Set interactive's initial boost target to **998.4 MHz**, keeping the full **1.2096 GHz** maximum available. This can reduce power use during short CPU bursts. [Apply it on the current V2 with Magisk](docs/CPU-BOOST-DEFAULT.md).
* **Balanced target-load tuning:** Raise the 998.4 MHz target-load entry from **60% to 65%**, allowing moderate work to remain at that frequency longer.
* **Earlier GPU idle transition:** Reduce the idler threshold from **10 to 3 checks**, shortening the wait before deeper GPU power saving.
* **Prompt first-touch response:** Restore a brief **800 MHz CPU input floor for 40 ms**, then release it so normal idle can return to 200 MHz.
* **Profile-aware CPU/GPU control:** An optional [Power HAL extension](docs/POWER-PROFILES.md) applies battery tuning in Balanced and raises active CPU/GPU frequency floors in Performance, retaining hardware sleep and existing thermal protection.
* **Kernel work and size reductions:** [E006 and kernel cleanup](docs/E006-KERNEL-WORK.md) remove unused scheduler bookkeeping and optional debug/profiling overhead, while reducing repeated zRAM history writes.

These changes are on the development branch; installing the original V2 release does not include them.

## 🐛 Known Bugs

1. **Aggressive CPU Scaling (Battery Drain):** The original V2 kernel favors high CPU speeds. The development branch lowers the initial boost target while retaining maximum clocks; further work focuses on power use during normal activity.
2. **GCam Go Front Video Viewfinder:** When recording video with the front camera, the live viewfinder displays a half-black/split-screen layout. **This is strictly a visual UI/hardware-stride bug.** The actual video file records perfectly in standard 16:9 HD without any corruption or black bars.

---

## 📝 Notice & Future Plans

* At this point, the OS and framework are fully optimized. The only remaining areas for improvement are deep kernel-level optimizations to balance the aggressive CPU scaling for better battery life, which is currently outside my scope.
* **I am actively shifting my development focus toward an Android 16 (LineageOS 23.2) port for the Oppo A37 series.** Because of this transition, please expect fewer updates to this Android 10 build in the near future. 

---

## 🛠️ Installation Instructions

**Prerequisites:** Unlocked Bootloader & TWRP Recovery installed.

1. Boot into TWRP Recovery.
2. **CRITICAL:** Go to Wipe -> Advanced Wipe -> Select **Dalvik / ART Cache, Cache, System, and Data**, then swipe to wipe. *(Do not dirty flash!)*
3. Go to Install, locate the `Lineage_17.1_REMASTERED.zip` ROM file, and swipe to flash.
4. *(Optional)* Flash your preferred ARM64 Android 10 GApps package.
5. Reboot to System.
