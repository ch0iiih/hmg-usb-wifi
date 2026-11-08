// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;

final class UsbEvents {
    static String action(String subsystem, String action, String deviceType,
                         String product, String devicePath, String networkInterface) {
        if ("usb".equals(subsystem) && "usb_device".equals(deviceType) && matchesAdapter(product)) {
            if ("remove".equals(action)) return "detach";
            if ("add".equals(action) || "change".equals(action)) return "update";
        }
        if ("net".equals(subsystem) && "wlan0".equals(networkInterface)) return "snapshot";
        if ("block".equals(subsystem) && devicePath != null && devicePath.contains("/usb")
                && ("add".equals(action) || "change".equals(action))) return "mount";
        return null;
    }

    private static boolean matchesAdapter(String product) {
        if (product == null) return false;
        String[] fields = product.split("/");
        if (fields.length < 2) return false;
        try {
            return Integer.parseInt(fields[0], 16) == 0x2357
                    && Integer.parseInt(fields[1], 16) == 0x012e;
        } catch (NumberFormatException ignored) {
            return false;
        }
    }
}
