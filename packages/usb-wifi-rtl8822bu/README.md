# USB Wi-Fi Driver for Archer T3U Nano

Experimental build 0.1.7 for Gen5W systems and USB device 2357:012e.
Model and firmware-date filtering are removed. The captured LX2PE kernel configuration and exact
original-driver checksum still define the compiled driver compatibility.

1. Remove USB WiFi Hotspot Enabler in NEMESIS and restart the head unit.
2. Import this ZIP through HMG-API, enable the mod, apply changes, and restart the unit.
3. Turn USB ADB off. Remove the USB drive, insert the T3U Nano, and wait 30 seconds.
4. Remove the adapter, insert the USB drive containing USB-WIFI-LOGS, and wait 15 seconds.
5. Read USB-WIFI-LOGS on the computer. last-adapter.txt retains the connected-device snapshot.

The engine checks the original driver checksum before replacing /system/wifi/bcmdhd.ko.
Disabling the mod and applying changes restores the original file. Restart after restoration.

The monitor receives kernel USB and network events through Android UEventObserver.
It checks already connected devices once at startup and attempts a load once per
adapter insertion. It waits for events while idle. Media mount broadcasts and
filesystem events trigger USB log export. Short, finite follow-ups after insertion
allow device initialization and mounting to complete.

The prior USB power-control parameter is restored when the adapter is removed or
the monitor stops. FileObserver handles writes to the parameter while connected.
The saved parameter survives monitor restarts in the same boot. The Android event
subscriptions and sysfs notifications still require vehicle testing.

This build provides the Wi-Fi driver and stock HAL parameter interface. Wireless
projection configuration and connection still need vehicle testing. The host tests
cover file restoration and monitor behavior. They do not establish vehicle stability.

The ARMv7 module has the same vermagic as the captured stock module. All 198 required
symbols are exported by the captured kernel. Of 539 named types represented in both
modules' debug information, 538 match. linux_mib differs and has no direct use found
in the driver source. Function signatures and types absent from the debug information
remain outside this comparison.

Driver source and license are available at https://github.com/morrownr/88x2bu-20210702
at commit 418d71cc00cd18b4a671f8c49ecce9b19cbfd3c9. The local source bundle includes the
driver archive and integration patch. The community kernel comes from
https://github.com/C457/android_kernel_telechips_tcc897x at
3402d473aed6a2b82c5d08e0ceafc4a54701a4a0. Mobis HAL integration follows the approach in
https://github.com/Open-HMG/HMG-API/pull/104.

Build 0.1.2 captures complete kernel logs, network counters, PHY entries, and
service logs. Driver info logging is enabled for the adapter test.

Build 0.1.3 captures Wi-Fi state transitions from the full log buffer and system
Wi-Fi settings code for client-mode analysis.

Build 0.1.4 retries an unbound T3U Nano interface at most three times after
startup or attachment when wlan0 is absent. It leaves bound devices alone.

Build 0.1.6 removes the firmware-date filter. KOR region filtering and the exact
original-driver checksum remain. Tested hardware is the Korean LX2 PE on 260902;
removing metadata filters does not establish other-firmware kernel compatibility.

Build 0.1.7 removes the KOR installation filter. No model, firmware-date or region
metadata filter remains. The native module is unchanged, including its KR regulatory
configuration. Other-region driver, kernel and framework compatibility is unverified.
