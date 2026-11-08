# Build and verification

## Native driver

The complete vendor source is in `driver-build/downloads/driver.tar.gz`.
`driver-build/driver-changes.patch` records the local changes. The pinned kernel
and Ubuntu root filesystem URLs and SHA256 digests are in
`driver-build/source-versions.json`. Download those two archives into
`driver-build/downloads/` and verify all digests before building.

In an ARM64 Linux guest, mount `driver-build/` at `/mnt/hmg` and run
`build-in-vm.sh` as root. The script uses an isolated Ubuntu 16.04 root filesystem
and GCC 4.9, applies the kernel ABI adjustments and driver patch, and places
the module and its debug version under `driver-build/build/`. Copy the stripped
module to `packages/usb-wifi-rtl8822bu/files/bcmdhd-rtl8822bu.ko`.

The kernel configuration retains its original capture name `lx2pe-260902.config`;
this describes the build baseline, not an installer firmware-date restriction.

## Android components

Set `ANDROID_JAR` to Android API 19's `android.jar` and `D8` to the Android SDK
`d8` executable. With a JDK supporting `javac --release 8`, run:

```sh
sh event-monitor/build.sh "$PWD/packages/usb-wifi-rtl8822bu/monitor.jar"
cp packages/usb-wifi-rtl8822bu/monitor.jar packages/wifi-client-test/client.jar
```

For the client hook, set `HMG_RUNTIME` to compiled HMG-API runtime classes and
`R8_JAR` to the Android R8 JAR, in addition to `ANDROID_JAR`, then run:

```sh
sh client-hooks/build.sh "$PWD/packages/wifi-client-test/hooks.jar"
```

Framework stubs are compile-only and are excluded from the output DEX.

## Package signing

Obtain the HMG-API 1.0.2 Java engine and set `HMGAPI_ENGINE_CLASSES` to its compiled
classes. Use your own author key following HMG-API's author signing instructions.
Keep that private key outside this repository. The packaging command is:

```sh
python3 tools/package.py /absolute/path/to/your-author.key
```

This signs both package directories, verifies their signatures, and writes
versioned installation ZIPs to `dist/`.

## Host tests

Set `HMGAPI_ENGINE_CLASSES` as above and `HMGAPI_TEST_STOCK` to your privately
captured stock `bcmdhd.ko`. The OEM module is not redistributed here.

```sh
python3 test-package.py
python3 test-client-package.py
python3 test-monitor.py
HMGAPI_TEST_PRODUCT=CVEV.USA.0000.V039.001.261001 python3 test-package.py
HMGAPI_TEST_PRODUCT=CVEV.USA.0000.V039.001.261001 python3 test-client-package.py
```

The alternative product string tests removed metadata restrictions in a simulated
filesystem. It does not validate the kernel, hook map, or Wi-Fi on that vehicle.
The tests check checksum refusal, exact original-file restoration, conflicting
projection modes, Wi-Fi flags, finite retry behavior and USB event handling.

To repeat the static ABI comparison, install `pyelftools`, set
`HMGAPI_TEST_KERNEL` to the privately captured `vmlinux.elf`, and run
`python3 check-module.py` after a native build. The included compatibility report
compares the original LX2 capture. It cannot prove runtime compatibility and does
not cover all pointer targets or function signatures.
