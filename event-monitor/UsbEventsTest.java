// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;

public final class UsbEventsTest {
    private static void check(String expected, String actual) {
        if (expected == null ? actual != null : !expected.equals(actual))
            throw new AssertionError("Expected " + expected + ", got " + actual);
    }

    public static void main(String[] args) {
        check("update", UsbEvents.action("usb", "add", "usb_device", "2357/12e/210", null, null));
        check("detach", UsbEvents.action("usb", "remove", "usb_device", "2357/012E/210", null, null));
        check(null, UsbEvents.action("usb", "remove", "usb_interface", "2357/12e/210", null, null));
        check(null, UsbEvents.action("usb", "add", "usb_device", "2357/11e/210", null, null));
        check(null, UsbEvents.action("usb", "add", "usb_device", "invalid", null, null));
        check(null, UsbEvents.action("usb", "add", "usb_device", null, null, null));
        check("snapshot", UsbEvents.action("net", "add", null, null, null, "wlan0"));
        check(null, UsbEvents.action("net", "change", null, null, null, "rmnet0"));
        check("mount", UsbEvents.action("block", "add", null, null, "/devices/usb2/block/sda", null));
        check(null, UsbEvents.action("block", "add", null, null, "/devices/mmcblk0", null));
        System.out.println("PASS USB device, interface, network, and storage event routing");
    }
}
