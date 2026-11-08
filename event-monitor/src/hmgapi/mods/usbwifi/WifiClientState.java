// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;

import android.os.Handler;
import android.os.Looper;
import android.os.UEventObserver;
import java.io.File;
import java.io.FileInputStream;

/** Publishes the existing USB driver's readiness to the stock Wi-Fi HAL. */
public final class WifiClientState {
    private final Handler handler = new Handler();
    private boolean announced;

    static boolean ready(File root) {
        File network = new File(root, "sys/class/net/wlan0");
        if (!network.exists()) return false;
        if (!"live".equals(read(new File(root, "sys/module/bcmdhd/initstate")))) return false;
        String mac = read(new File(root, "sys/module/bcmdhd/parameters/mac_address_read"));
        if (!mac.matches("(?i)([0-9a-f]{2}:){5}[0-9a-f]{2}")
                || mac.equals("00:00:00:00:00:00") || mac.equalsIgnoreCase("ff:ff:ff:ff:ff:ff")) return false;
        try {
            File device = new File(network, "device").getCanonicalFile().getParentFile();
            return "2357".equals(read(new File(device, "idVendor")))
                    && "012e".equals(read(new File(device, "idProduct")));
        } catch (java.io.IOException error) {
            return false;
        }
    }

    private static String read(File file) {
        try {
            FileInputStream stream = new FileInputStream(file);
            try {
                byte[] bytes = new byte[128];
                int count = stream.read(bytes);
                return count <= 0 ? "" : new String(bytes, 0, count, "UTF-8").trim();
            } finally { stream.close(); }
        } catch (java.io.IOException error) {
            return "";
        }
    }

    private void update() {
        try {
            Class<?> properties = Class.forName("android.os.SystemProperties");
            String status = (String) properties.getMethod("get", String.class, String.class)
                    .invoke(null, "wlan.driver.status", "");
            if (!announced && ready(new File("/"))) {
                properties.getMethod("set", String.class, String.class)
                        .invoke(null, "wlan.driver.status", "ok");
                announced = true;
                System.out.println("USB client driver ready; wlan.driver.status " + status + " -> ok");
            } else if (announced && !new File("/sys/class/net/wlan0").exists()) {
                if ("ok".equals(status)) properties.getMethod("set", String.class, String.class)
                        .invoke(null, "wlan.driver.status", "unloaded");
                announced = false;
                System.out.println("USB client interface removed");
            }
        } catch (Exception error) {
            System.err.println("Could not publish USB client driver readiness: " + error);
        }
    }

    private void checkAfter(long delay) {
        handler.postDelayed(new Runnable() {
            @Override public void run() { update(); }
        }, delay);
    }

    public static void main(String[] args) {
        Looper.prepareMainLooper();
        final WifiClientState service = new WifiClientState();
        UEventObserver observer = new UEventObserver() {
            @Override public void onUEvent(UEvent event) {
                if (!"wlan0".equals(event.get("INTERFACE"))) return;
                service.checkAfter(0);
                service.checkAfter(500);
                service.checkAfter(2000);
            }
        };
        observer.startObserving("SUBSYSTEM=net");
        service.checkAfter(0);
        service.checkAfter(1500);
        System.out.println("Wi-Fi Client Test driver-state service ready");
        Looper.loop();
    }
}
