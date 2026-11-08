# HMG USB Wi-Fi

**English** | [한국어](README.ko.md)

Experimental HMG-API mods for using a TP-Link Archer T3U Nano USB Wi-Fi adapter with Hyundai/Kia Gen5W head units, plus diagnostics for the stock Wi-Fi client.

## Downloads

Get the signed installation ZIPs from the [releases page](https://github.com/ch0iiih/hmg-usb-wifi/releases).

| Package | Version | Purpose |
| --- | --- | --- |
| [USB Wi-Fi Driver](dist/usb-wifi-rtl8822bu-0.1.7.zip) | 0.1.7 | RTL8822BU driver, stock HAL integration, event monitoring and USB diagnostics |
| [Wi-Fi Client Test](dist/wifi-client-test-0.1.5.zip) | 0.1.5 | Stock Wi-Fi client diagnostics; external-network scanning and connection remain unverified |

## Features

- Driver integration for the tested Archer T3U Nano, USB ID `2357:012e`.
- USB and network events with limited initialization retries, without continuous polling while idle.
- Saves the existing USB power-control setting and restores it on adapter removal or service shutdown.
- Exports driver, kernel and framework diagnostics to a USB drive.
- Uses HMG-API's baseline driver check and original-file restoration.
- Optional Client Test preserves Wi-Fi settings feature flags, announces driver readiness only after the interface is ready, and guards the T3U against wired Android Auto accessory negotiation.

Wireless phone projection itself and automatic AP/client switching are **not included**. A separate compatible projection mod and configuration are required for wireless CarPlay.

## Compatibility and current status

| Item | Scope |
| --- | --- |
| HMG-API | 1.0.2 or newer |
| Installation filters | No model, firmware-date or region filter |
| Tested vehicle | Korean-market Palisade LX2 PE, firmware `260902` |
| Tested adapter | Archer T3U Nano, USB `2357:012e`, RTL8822BU family |
| Native build baseline | ARMv7, Linux `3.18.24-tcc`, captured LX2 PE kernel configuration |
| Wireless CarPlay | Connected in the test vehicle using a separate projection mod |
| Stock external Wi-Fi client | Wi-Fi switch and MAC became available |

**Model, firmware-date and region filters are removed. This does not establish compatibility with other vehicles or firmware builds.** Adapter revisions can also use different USB IDs or chipsets under the same product name.

HMG-API checks an existing `/system/wifi/bcmdhd.ko` against baseline MD5 `ac5bff41f934c996eff5208dbcd9550f` before replacing it. A different original file is rejected. This file check does not validate the entire running kernel ABI. Client Test also needs a suitable HMG-API hook map; removing an installer filter does not create one.

The native module retains its **KR country/channel configuration**. Removing the installation region filter does not change radio settings. Other-region kernel, driver and framework behavior remain unverified.

## Installation

1. If NEMESIS USB WiFi Hotspot Enabler is installed, uninstall it and restart the head unit first.
2. Install the USB Wi-Fi Driver ZIP in HMG-API, enable it, then select **Apply changes → Restart Unit**.
3. Turn off USB ADB and connect the tested T3U Nano. Configure a separate compatible projection mod if using wireless CarPlay.
4. To test external Wi-Fi instead, also install Client Test. Disable **Wireless Phone Projection** and **Wireless CarPlay + Android Auto**, enable **Wi-Fi Client Test**, and apply/restart.
5. Open stock Wi-Fi settings, turn Wi-Fi on manually, and check for access points. Turning Wi-Fi off on the phone alone does not stop the head unit's AP.

Client Test cannot be enabled alongside the projection mods above. To return to wireless CarPlay, disable Client Test, enable the projection mod, and apply/restart.

## Diagnostics and restoration

Create `USB-WIFI-LOGS` on a USB drive, connect it to the head unit, and allow time for export. `last-adapter.txt` retains a snapshot from when the adapter was connected. Logs can contain device identifiers; review them before posting publicly. System components may also be captured for offline diagnosis. This repository contains no private vehicle logs or OEM binaries.

To restore the original driver, disable the driver mod and apply changes in HMG-API, then restart. HMG-API restores its backed-up original file.

## Source and building

- `event-monitor/`: event monitor and driver readiness service.
- `client-hooks/`: USB accessory guard and its test.
- `packages/`: package definitions and service scripts.
- `driver-build/`: pinned vendor source inputs, integration patch, captured kernel configuration and build script.
- `dist/`: signed installation ZIPs and SHA256 digests.

See [BUILD.md](BUILD.md) for build inputs, signing and host tests. Rebuilt packages must be signed with your own HMG-API author key. No private signing key is included.

## Credits and licenses

- Realtek driver and integration patch: GPL-2.0. [morrownr/88x2bu-20210702](https://github.com/morrownr/88x2bu-20210702), commit `418d71cc00cd18b4a671f8c49ecce9b19cbfd3c9`.
- Kernel build base: [C457/android_kernel_telechips_tcc897x](https://github.com/C457/android_kernel_telechips_tcc897x), commit `3402d473aed6a2b82c5d08e0ceafc4a54701a4a0`.
- USB/HAL integration approach: dibble9012's [HMG-API PR #104](https://github.com/Open-HMG/HMG-API/pull/104).
- Local Java services, hooks and host tools: AGPL-3.0. Existing upstream notices remain intact. Full license texts are under `LICENSES/`.

## Changelog

- **Driver 0.1.7 / Client Test 0.1.5:** remove the KOR installation filter; retain original-driver checks and existing KR channel configuration.

- **Driver 0.1.6 / Client Test 0.1.4:** remove firmware-date filtering; retain KOR filtering and the original-driver check.
- **Driver 0.1.5 / Client Test 0.1.3:** remove model filtering.
- **Driver 0.1.4:** bounded retries for an unbound T3U interface; bound interfaces remain untouched.
- **Client Test 0.1.2:** Android Auto accessory guard for T3U. Its effect on the failed client scan needs vehicle verification.
