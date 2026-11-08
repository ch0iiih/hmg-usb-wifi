#!/system/bin/sh
export PATH=/data/hmgapi/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
umask 077
STATE=/data/local/tmp/hmg-usb-wifi-rtl8822bu
POWER=/sys/module/tcc_dwc_otg/parameters/vbus_control_enable
mkdir -p "$STATE" || exit 1
boot=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)
if [ "$(cat "$STATE/boot-id" 2>/dev/null)" != "$boot" ]; then
    rm -f "$STATE/power-before" "$STATE/attempted" "$STATE/repair-count"
    echo "$boot" > "$STATE/boot-id"
fi

restore_power() {
    if [ -r "$STATE/power-before" ] && [ -w "$POWER" ]; then
        cat "$STATE/power-before" > "$POWER"
        rm -f "$STATE/power-before"
    fi
}
trap 'exit 1' HUP INT TERM

log() {
    echo "$(date) boot=$boot $*" >> "$STATE/driver.log"
    echo "$*"
}

snapshot() {
    {
        echo "version=0.1.7"
        echo "captured=$(date)"
        echo "product=$(getprop ro.build.product)"
        echo "boot=$boot"
        echo "adapter=$present"
        echo '--- modules ---'
        cat /proc/modules
        echo '--- interfaces ---'
        ls -l /sys/class/net
        echo '--- bcmdhd parameters ---'
        for key in mac_address_read iface_name rtw_country_code; do
            echo "$key"
            cat "/sys/module/bcmdhd/parameters/$key" 2>/dev/null
            echo
        done
        echo '--- USB identity ---'
        if [ -n "$present" ]; then
            for key in idVendor idProduct bcdDevice product manufacturer; do
                echo "$key"
                cat "$present/$key" 2>/dev/null
            done
            ls -l "$present/"*/driver 2>/dev/null
        fi
        echo '--- network addresses ---'
        ip addr show dev wlan0 2>&1
        echo '--- kernel network device counters ---'
        cat /proc/net/dev 2>&1
        echo '--- all network links ---'
        ip link show 2>&1
        echo '--- wireless PHYs ---'
        ls -l /sys/class/ieee80211 2>&1
        echo '--- driver proc entries ---'
        ls -l /proc/net/rtl88x2bu 2>&1
        echo '--- Wi-Fi framework properties ---'
        getprop wifi.interface
        getprop wlan.driver.status
        echo '--- framework service processes ---'
        ps | grep -iE 'wifi|supplicant|hostapd|netd|dhcp'
        echo '--- global Wi-Fi switch ---'
        settings get global wifi_on 2>&1
        echo '--- USB port control ---'
        cat "$POWER" 2>/dev/null
        echo "captured_end=$(date)"
        echo 'finished=1'
    } > "$STATE/current.txt.part"
    mv "$STATE/current.txt.part" "$STATE/current.txt"
    dmesg > "$STATE/kernel-full.txt"
    if [ -n "$present" ] && [ "$(cat "$present/idVendor" 2>/dev/null)" = 2357 ] &&
       [ "$(cat "$present/idProduct" 2>/dev/null)" = 012e ]; then
        cp "$STATE/current.txt" "$STATE/last-adapter.txt"
        cp "$STATE/kernel-full.txt" "$STATE/last-adapter-kernel.txt"
    fi
    dmesg | grep -iE '88x2|8822|2357|012e|bcmdhd|wlan|usb [0-9-]+:|unknown symbol|oops|bug:|call trace' \
        > "$STATE/kernel-wifi.txt"
}

action=${1:-update}
if [ "$action" = startup ] || [ "$action" = detach ]; then
    restore_power
    rm -f "$STATE/attempted" "$STATE/repair-count"
fi
case "$action" in
    shutdown)
        restore_power
        exit 0
        ;;
    guard)
        if [ -f "$STATE/power-before" ] && [ -w "$POWER" ]; then
            [ "$(cat "$POWER")" = 0 ] || echo 0 > "$POWER"
        fi
        exit 0
        ;;
esac
log "event=$action"
present=
for device in /sys/bus/usb/devices/*; do
    if [ "$(cat "$device/idVendor" 2>/dev/null)" = 2357 ] &&
       [ "$(cat "$device/idProduct" 2>/dev/null)" = 012e ]; then
        present=$device
        break
    fi
done

if [ -n "$present" ]; then
    level=/sys/module/bcmdhd/parameters/rtw_drv_log_level
    if [ -w "$level" ] && [ "$(cat "$level")" != 4 ]; then
        echo 4 > "$level"
    fi
    if [ -w "$POWER" ]; then
        [ -f "$STATE/power-before" ] || cat "$POWER" > "$STATE/power-before"
        [ "$(cat "$POWER")" = 0 ] || echo 0 > "$POWER"
    fi
    if [ ! -f "$STATE/attempted" ]; then
        touch "$STATE/attempted"
        if grep -q '^88x2bu ' /proc/modules; then
            log 'Legacy 88x2bu is loaded. Remove USBWifi Hotspot Enabler and restart the unit'
        elif [ ! -d /sys/module/bcmdhd ]; then
            log 'Adapter connected. Loading bcmdhd with iface_name=wlan0 rtw_drv_log_level=4'
            insmod /system/wifi/bcmdhd.ko iface_name=wlan0 rtw_drv_log_level=4 >> "$STATE/driver.log" 2>&1
            log "insmod_exit=$?"
        else
            log 'Adapter connected. bcmdhd is already loaded'
        fi
    fi
else
    restore_power
    rm -f "$STATE/attempted" "$STATE/repair-count"
fi

if [ "$action" = repair ] && [ -n "$present" ] && [ ! -e /sys/class/net/wlan0 ] &&
   [ -w /sys/bus/usb/drivers/rtl88x2bu/bind ]; then
    count=$(cat "$STATE/repair-count" 2>/dev/null)
    case "$count" in [0123]) ;; *) count=0 ;; esac
    if [ "$count" -lt 3 ]; then
        for interface in "$present/"*:*; do
            [ -d "$interface" ] || continue
            [ ! -e "$interface/driver" ] || continue
            [ "$(cat "$interface/bInterfaceClass" 2>/dev/null)" = ff ] || continue
            count=$((count+1))
            echo "$count" > "$STATE/repair-count"
            name=${interface##*/}
            log "Retrying unbound USB interface $name (attempt $count of 3)"
            echo "$name" > /sys/bus/usb/drivers/rtl88x2bu/bind 2>> "$STATE/driver.log"
            log "bind_exit=$?"
            break
        done
    fi
fi


snapshot
folders=
for folder in /storage/usb[012]/USB-WIFI-LOGS; do
    [ -d "$folder" ] || continue
    folders="$folders $folder"
done
if [ -n "$folders" ]; then
    logcat -d -v threadtime 2>/dev/null | grep -iE 'wi.?fi|wpa_|supplicant|nl80211|dhcp|softap|wlan.driver' \
        > "$STATE/framework-wifi.log"
    dumpsys wifi 2>/dev/null | grep -iE 'current state|mWifiState|mNetworkInfo|mWifiInfo|mSupplicantState|LinkProperties|interface|StateMachine' \
        > "$STATE/framework-state.txt"
    if [ -r /data/hmgapi/logs/usb-wifi-rtl8822bu/driver-monitor.log ]; then
        cat /data/hmgapi/logs/usb-wifi-rtl8822bu/driver-monitor.log > "$STATE/monitor-service.log"
    fi
    if [ -r /data/hmgapi/logs/wifi-client-test/driver-state.log ]; then
        cat /data/hmgapi/logs/wifi-client-test/driver-state.log > "$STATE/client-state-service.log"
    fi
fi
for folder in $folders; do
    for name in driver.log current.txt last-adapter.txt kernel-wifi.txt kernel-full.txt last-adapter-kernel.txt framework-wifi.log framework-state.txt monitor-service.log client-state-service.log; do
        [ -r "$STATE/$name" ] || continue
        if cat "$STATE/$name" > "$folder/.$name.part"; then
            mv "$folder/.$name.part" "$folder/$name"
        fi
    done
    # Capture system code for offline client-mode analysis once on this USB drive.
    app=$(pm path com.hkmc.wifisettings 2>/dev/null)
    apk=${app#package:}
    case "$apk" in
        /system/app/*.apk|/system/priv-app/*.apk|/vendor/app/*.apk)
            for source in "$apk" "${apk%.apk}.odex"; do
                [ -r "$source" ] || continue
                name=${source##*/}
                [ -s "$folder/$name" ] && continue
                if cat "$source" > "$folder/.$name.part"; then
                    mv "$folder/.$name.part" "$folder/$name"
                fi
            done
            ;;
    esac
    for source in /system/lib/libhardware_legacy.so /system/framework/wifi-service.jar /system/framework/wifi-service.odex; do
        [ -r "$source" ] || continue
        name=${source##*/}
        [ -s "$folder/$name" ] && continue
        if cat "$source" > "$folder/.$name.part"; then
            mv "$folder/.$name.part" "$folder/$name"
        fi
    done
done
[ -z "$folders" ] || sync
exit 0
