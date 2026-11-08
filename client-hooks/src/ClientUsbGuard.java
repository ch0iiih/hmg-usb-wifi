// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;

import android.content.ComponentName;
import android.content.Intent;
import android.hardware.usb.UsbDevice;
import hmgapi.hook.LoadedApp;
import hmgapi.hook.MethodHook;
import hmgapi.hook.ModContext;
import hmgapi.hook.ModEntry;

public final class ClientUsbGuard extends ModEntry {
    static boolean block(String service, int startMode, int vendor, int product) {
        return "com.google.android.projection.service.GalReceiverService".equals(service)
                && startMode == 1 && vendor == 0x2357 && product == 0x012e;
    }

    @Override
    public void appLoaded(final ModContext mod, LoadedApp app) {
        if (!"com.google.android.projection.sink".equals(app.packageName)) return;
        mod.hook(null, "framework.context_impl.start_service", new MethodHook() {
            @Override
            protected void beforeHookedMethod(Param call) {
                Intent intent = (Intent) call.args[0];
                ComponentName component = intent == null ? null : intent.getComponent();
                if (component == null) return;
                UsbDevice device = intent.getParcelableExtra("device");
                if (device == null || !block(component.getClassName(), intent.getIntExtra("startMode", -1),
                        device.getVendorId(), device.getProductId())) return;
                call.setResult(null);
                mod.log("Skipped Android Auto accessory negotiation for Archer T3U Nano");
            }
        });
        mod.log("T3U Nano accessory negotiation guard installed in " + app.processName);
    }
}
