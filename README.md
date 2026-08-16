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
* **Reduced RAM Usage:** Saved around **100MB of RAM** by disabling background caching for heavy apps like the Camera and Browser.
* **Heavy Debloat:** Removed useless LineageOS system APKs that most people never use.
* **Media & Customization Purge:** Removed redundant fonts, extra languages, system wallpapers, and heavy ringtones/notification sounds. (It's much easier to just download a picture from your gallery to set as a wallpaper or download your own ringtones). *Note: Customization options are reduced, but you can always restore fonts via root packages.*

### App & UI Upgrades
* **Google Dialer:** Replaced the stock dialer with the Google Dialer for its advanced features. 
  *(⚠️ **Warning:** If you open it and see a "Device Unsupported" popup, just ignore it. It happens because the ROM doesn't have Google Mobile Services pre-installed. The dialer will still work perfectly for calls, and if you flash a GApps package, the popup goes away).*
* **Updated Core Apps:** Updated all included APKs to their latest supported versions, especially the Android System WebView, so modern websites load correctly.
* **Lighter Keyboard:** Replaced the heavy default AOSP keyboard with a much lighter, faster version.
* **Audio Boost:** Natively boosted the system sound volume.
* **Classic Hardware Keys:** Restored the old, highly requested menu button behavior (**1 Press** = Recents Panel, **Long Press** = Split-screen multitasking).

### Under-The-Hood Tweaks
* **3-in-1 Flash:** The `fix_baseband` patch (for cellular/RIL) and the custom kernel are already baked directly into this ROM. One flash gets you everything.
* **Lower CPU Idle:** The CPU can now idle at its absolute minimum of **200MHz** (instead of being capped at 400MHz) to save standby power.
* **Battery Accuracy:** Fixed the internal battery profile to match the exact physical capacity of the A37's battery for much better battery level reporting.
* **Hardware Brightness Fix:** Calibrated internal framework values to fix the auto-brightness and brightness slider so it perfectly matches the phone's physical LCD limits.
* **Native System Optimizations:** Tweaked default system settings to disable heavy wakelocks and battery-draining features right out of the box.
* **Prop Tweaks:** Added multiple `build.prop` and `default.prop` tweaks to improve UI rendering, sleep policies, and overall responsiveness.
* **Network & Memory:** Optimized Wi-Fi and cellular connections, alongside improvements to Qualcomm memory management and CPU governor algorithms.
* **Telemetry Disabled:** Disabled redundant system loggers to save background CPU cycles.

---

## 🐛 Known Bugs

1. **Aggressive CPU Scaling (Battery Drain):** The included custom kernel is very aggressive with CPU speeds. It makes the phone feel fast, but it costs a bit more battery life. Since this is a kernel-level trait, it's not currently up to me to fix.
2. **Camera Video Recording Glitch:** Recording video currently does not work properly. It seems to be related to some GPU optimizations I made. The video glitches out, often merging recent frames or showing a single frame from 2 seconds ago continuously. 

---

## 📝 TODO List

* [ ] Fix the camera video recording bug.
* [ ] Fork the custom kernel and optimize it to get better battery life (focusing on battery rather than pure aggressive smoothness, which might cause a slight drop in UI speed but is worth it for screen-on time).

---

## 🛠️ Installation Instructions

**Prerequisites:** Unlocked Bootloader & TWRP Recovery installed.

1. Boot into TWRP Recovery.
2. **CRITICAL:** Go to Wipe -> Advanced Wipe -> Select **Dalvik / ART Cache, Cache, System, and Data**, then swipe to wipe. *(Do not dirty flash!)*
3. Go to Install, locate the `Lineage_17.1_REMASTERED.zip` ROM file, and swipe to flash.
4. *(Optional)* Flash your preferred ARM64 Android 10 GApps package.
5. Reboot to System.
