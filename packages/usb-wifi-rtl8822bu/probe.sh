#!/system/bin/sh
set -eu
root=${HMGAPI_ROOT:-}
if [ -f "$root/data/nemesis/apps/usbwifi.hotspot/svc/usbwifi-hotspot-daemon.sh" ]; then
    echo 'Remove USBWifi Hotspot Enabler in NEMESIS and restart the unit before applying this driver.' >&2
    exit 1
fi
if [ -r "$root/proc/modules" ] && grep -q '^88x2bu ' "$root/proc/modules"; then
    echo 'The old 88x2bu module is still loaded. Remove USBWifi Hotspot Enabler and restart the unit.' >&2
    exit 1
fi
echo '{"changes":[]}'
