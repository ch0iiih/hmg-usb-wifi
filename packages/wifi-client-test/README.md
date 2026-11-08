# Wi-Fi Client Test

Keep USB Wi-Fi Driver enabled and update it to 0.1.6 or later. Disable Wireless
Phone Projection and Wireless CarPlay + Android Auto. Enable this test mod, apply
changes, and restart the unit. Insert the T3U Nano, open the stock Wi-Fi settings,
and enable Wi-Fi manually. Check for an access-point list and connection.

This mod provides the Wi-Fi feature flags and rejects simultaneous projection
mods. The driver service exports diagnostics when the USB drive is reconnected.

To return to wireless CarPlay, disable this test mod, enable Wireless Phone
Projection, apply changes, and restart. This is a client-mode diagnostic stage.
External-network connection has not been established in the vehicle yet.

Build 0.1.1 publishes wlan.driver.status=ok once the T3U Nano interface,
valid MAC address, and live bcmdhd module are confirmed. It uses startup and
network events and leaves subsequent driver-state changes to the framework.

Build 0.1.2 carries the T3U Nano USB-accessory guard while the projection mod is
disabled. It skips the wired Android Auto start intent for USB 2357:012e.
Successful AP operation used the equivalent guard in the projection mod.
Vehicle logs show accessory requests 51/52 before the failed scan test.
Blocking those requests is a targeted compatibility change and needs retesting.

Build 0.1.3 removes the model filter. The package targets KOR firmware 260902.
Other models still need driver and framework compatibility verification.

Build 0.1.4 removes the firmware-date filter and requires USB Wi-Fi Driver 0.1.6.
KOR region filtering remains. Other firmware builds need driver ABI and HMG-API
hook-map compatibility validation; client scanning and connection remain unverified.
