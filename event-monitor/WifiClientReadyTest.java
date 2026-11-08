// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;

public final class WifiClientReadyTest {
    private static void write(Path root, String name, String value) throws Exception {
        Path path = root.resolve(name);
        Files.createDirectories(path.getParent());
        Files.write(path, value.getBytes("UTF-8"));
    }

    private static void check(File root, boolean expected) {
        if (WifiClientState.ready(root) != expected) throw new AssertionError("Readiness expected " + expected);
    }

    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("wifi-ready-");
        try {
            check(root.toFile(), false);
            Path network = root.resolve("sys/class/net/wlan0");
            Files.createDirectories(network);
            Path device = root.resolve("sys/devices/usb/4-1/4-1:1.0");
            Files.createDirectories(device);
            Files.createSymbolicLink(network.resolve("device"), device);
            write(root, "sys/devices/usb/4-1/idVendor", "2357\n");
            write(root, "sys/devices/usb/4-1/idProduct", "012e\n");
            write(root, "sys/module/bcmdhd/initstate", "live\n");
            write(root, "sys/module/bcmdhd/parameters/mac_address_read", "cc:ba:bd:eb:6e:76\n");
            check(root.toFile(), true);
            write(root, "sys/module/bcmdhd/parameters/mac_address_read", "\n");
            check(root.toFile(), false);
            write(root, "sys/module/bcmdhd/parameters/mac_address_read", "00:00:00:00:00:00\n");
            check(root.toFile(), false);
            write(root, "sys/module/bcmdhd/parameters/mac_address_read", "cc:ba:bd:eb:6e:76\n");
            write(root, "sys/module/bcmdhd/initstate", "coming\n");
            check(root.toFile(), false);
            write(root, "sys/module/bcmdhd/initstate", "live\n");
            write(root, "sys/devices/usb/4-1/idProduct", "011e\n");
            check(root.toFile(), false);
            System.out.println("PASS client readiness requires live module, target USB interface, and valid MAC");
        } finally {
            Files.walk(root).sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                try { Files.delete(path); } catch (Exception error) { throw new RuntimeException(error); }
            });
        }
    }
}
