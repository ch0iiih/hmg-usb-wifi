// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;
public final class ClientUsbGuardTest {
    public static void main(String[] args) {
        String service="com.google.android.projection.service.GalReceiverService";
        if (!ClientUsbGuard.block(service,1,0x2357,0x012e)) throw new AssertionError("target adapter");
        if (ClientUsbGuard.block(service,0,0x2357,0x012e)) throw new AssertionError("other start mode");
        if (ClientUsbGuard.block("other.Service",1,0x2357,0x012e)) throw new AssertionError("other service");
        if (ClientUsbGuard.block(service,1,0x18d1,0x4ee7)) throw new AssertionError("phone");
        if (ClientUsbGuard.block(service,1,0x2357,0x011e)) throw new AssertionError("other adapter");
        if (ClientUsbGuard.block(null,1,0x2357,0x012e)) throw new AssertionError("missing service");
        System.out.println("PASS guard targets only T3U Nano wired-accessory negotiation");
    }
}
