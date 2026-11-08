#!/bin/sh
set -eu

# Run as root inside the project Lima guest. Output files are placed on its share.
ROOT=/opt/hmg-xenial
mkdir -p "$ROOT"
if [ ! -f "$ROOT/etc/os-release" ]; then
    tar -xzf /mnt/hmg/downloads/xenial-arm64.tar.gz -C "$ROOT"
fi
mkdir -p "$ROOT/dev" "$ROOT/proc" "$ROOT/in"
mountpoint -q "$ROOT/dev" || mount --bind /dev "$ROOT/dev"
mountpoint -q "$ROOT/proc" || mount -t proc proc "$ROOT/proc"
mountpoint -q "$ROOT/in" || mount --bind /mnt/hmg "$ROOT/in"
cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
cat > "$ROOT/etc/apt/sources.list" <<'SOURCES'
deb http://ports.ubuntu.com/ubuntu-ports xenial main universe
deb http://ports.ubuntu.com/ubuntu-ports xenial-updates main universe
SOURCES

chroot "$ROOT" /bin/sh -es <<'BUILD'
export DEBIAN_FRONTEND=noninteractive
if ! command -v arm-linux-gnueabi-gcc-4.9 >/dev/null; then
    apt-get update
    apt-get install -y --no-install-recommends gcc-4.9-arm-linux-gnueabi \
        binutils-arm-linux-gnueabi make bc gcc libc6-dev python patch perl ca-certificates
    ln -sf /usr/bin/arm-linux-gnueabi-gcc-4.9 /usr/bin/arm-linux-gnueabi-gcc
fi

export ARCH=arm CROSS_COMPILE=arm-linux-gnueabi-
mkdir -p /w/kernel /w/driver /in/build
if [ ! -f /w/kernel/Makefile ]; then
    tar -xzf /in/downloads/kernel.tar.gz --strip-components=1 -C /w/kernel
    # Match options selected by the TCC803X kernel but absent from this TCC897x tree.
    printf '\nconfig CAR_ABI\n\tdef_bool y\n\tselect ARCH_DMA_ADDR_T_64BIT\n\tselect ZONE_DMA\n\tselect MIGHT_HAVE_PCI\n' >> /w/kernel/arch/arm/Kconfig
    sed -i 's/u32 vmacache_seqnum;/u64 vmacache_seqnum;/' \
        /w/kernel/include/linux/mm_types.h /w/kernel/include/linux/sched.h
fi
cd /w/kernel
cp /in/lx2pe-260902.config .config
make olddefconfig
cp .config /in/build/resolved-kernel.config
make -j4 modules_prepare

# Always start with pristine driver sources before applying the recorded patch.
tar -xzf /in/downloads/driver.tar.gz --strip-components=1 -C /w/driver
cd /w/driver
patch -p1 < /in/driver-changes.patch
make -j4 KSRC=/w/kernel USER_MODULE_NAME=bcmdhd ldflags-y= \
    CONFIG_PLATFORM_AUTODETECT=n CONFIG_RTW_ANDROID=4 \
    CONFIG_LOAD_PHY_PARA_FROM_FILE=n CONFIG_POWER_SAVING=n \
    CONFIG_WIFI_MONITOR=n CONFIG_RTW_LOG_LEVEL=2 CONFIG_MP_INCLUDED=n \
    KCFLAGS='-g -DCONFIG_RTW_REGD_SRC=0 -DCONFIG_APPEND_VENDOR_IE_ENABLE -DCONFIG_LITTLE_ENDIAN -DCONFIG_IOCTL_CFG80211 -DRTW_USE_CFG80211_STA_EVENT' \
    modules
cp bcmdhd.ko /in/build/bcmdhd-rtl8822bu.debug.ko
arm-linux-gnueabi-strip --strip-debug -o /in/build/bcmdhd-rtl8822bu.ko bcmdhd.ko
arm-linux-gnueabi-readelf -h /in/build/bcmdhd-rtl8822bu.ko
arm-linux-gnueabi-gcc --version | head -1
sha256sum /in/build/bcmdhd-rtl8822bu.ko
BUILD
