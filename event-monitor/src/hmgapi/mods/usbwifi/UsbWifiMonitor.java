// SPDX-License-Identifier: AGPL-3.0-only
package hmgapi.mods.usbwifi;

import android.content.IIntentReceiver;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.FileObserver;
import android.os.Bundle;
import android.os.IBinder;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.UEventObserver;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public final class UsbWifiMonitor {
    private final Handler worker;
    private final File script;
    private final List<FileObserver> storageObservers = new ArrayList<FileObserver>();
    private final UEventObserver events;
    private final FileObserver powerObserver;
    private volatile boolean stopping;
    private IIntentReceiver mediaReceiver;

    private UsbWifiMonitor(File script) {
        this.script = script;
        HandlerThread thread = new HandlerThread("USBWiFiEvents");
        thread.start();
        worker = new Handler(thread.getLooper());
        events = new UEventObserver() {
            @Override public void onUEvent(UEvent event) {
                String action = UsbEvents.action(event.get("SUBSYSTEM"), event.get("ACTION"),
                        event.get("DEVTYPE"), event.get("PRODUCT"), event.get("DEVPATH"), event.get("INTERFACE"));
                if (action == null) return;
                if ("mount".equals(action)) {
                    mediaChanged();
                } else {
                    request(action, 0);
                    if ("update".equals(action)) {
                        request("snapshot", 1000);
                        request("snapshot", 3000);
                    }
                }
            }
        };
        powerObserver = new FileObserver("/sys/module/tcc_dwc_otg/parameters/vbus_control_enable",
                FileObserver.MODIFY | FileObserver.CLOSE_WRITE) {
            @Override public void onEvent(int event, String path) {
                request("guard", 0);
            }
        };
    }

    private void request(final String action, long delay) {
        if (stopping) return;
        worker.postDelayed(new Runnable() {
            @Override public void run() {
                if (stopping) return;
                runAction(action);
                if ("startup".equals(action) || "update".equals(action)) {
                    request("repair", 1000);
                    request("repair", 5000);
                    request("repair", 15000);
                }
                if (!"guard".equals(action)) watchStorage();
            }
        }, delay);
    }

    private void mediaChanged() {
        // Mount completion and HMG-API's log-directory creation are separate events.
        request("snapshot", 0);
        request("snapshot", 2000);
        request("snapshot", 8000);
    }

    private void runAction(String action) {
        try {
            Process process = new ProcessBuilder("/system/bin/sh", script.getPath(), action)
                    .redirectErrorStream(true).start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            try {
                String line;
                while ((line = reader.readLine()) != null) System.out.println(line);
            } finally {
                reader.close();
            }
            int result = process.waitFor();
            if (result != 0) System.err.println("USB Wi-Fi action " + action + " exited " + result);
        } catch (Exception error) {
            System.err.println("USB Wi-Fi action " + action + " failed: " + error);
        }
    }

    private void watchStorage() {
        for (FileObserver observer : storageObservers) observer.stopWatching();
        storageObservers.clear();
        for (final String directory : new String[]{"/storage", "/storage/usb0", "/storage/usb1", "/storage/usb2"}) {
            if (!new File(directory).isDirectory()) continue;
            FileObserver observer = new FileObserver(directory, FileObserver.CREATE | FileObserver.MOVED_TO) {
                @Override public void onEvent(int event, String path) {
                    if ("USB-WIFI-LOGS".equals(path)
                            || ("/storage".equals(directory) && path != null && path.matches("usb[012]"))) {
                        mediaChanged();
                    }
                }
            };
            storageObservers.add(observer);
            observer.startWatching();
        }
    }

    private void observeMedia() {
        try {
            Class<?> activityManager = Class.forName("android.app.IActivityManager");
            final Object manager = Class.forName("android.app.ActivityManagerNative")
                    .getMethod("getDefault").invoke(null);
            final Method finish = activityManager.getMethod("finishReceiver", IBinder.class,
                    int.class, String.class, Bundle.class, boolean.class);
            mediaReceiver = new IIntentReceiver.Stub() {
                @Override public void performReceive(Intent intent, int resultCode, String data,
                        Bundle extras, boolean ordered, boolean sticky, int sendingUser) {
                    mediaChanged();
                    if (ordered) {
                        try { finish.invoke(manager, asBinder(), resultCode, data, extras, false); }
                        catch (Exception error) { System.err.println("Finishing media broadcast failed: " + error); }
                    }
                }
            };
            IntentFilter filter = new IntentFilter();
            filter.addAction(Intent.ACTION_MEDIA_MOUNTED);
            filter.addAction(Intent.ACTION_MEDIA_UNMOUNTED);
            filter.addAction(Intent.ACTION_MEDIA_REMOVED);
            filter.addAction(Intent.ACTION_MEDIA_BAD_REMOVAL);
            filter.addDataScheme("file");
            activityManager.getMethod("registerReceiver", Class.forName("android.app.IApplicationThread"),
                    String.class, IIntentReceiver.class, IntentFilter.class, String.class, int.class)
                    .invoke(manager, null, null, mediaReceiver, filter, null, -1);
            System.out.println("USB media mount receiver registered");
        } catch (Exception error) {
            System.err.println("Media receiver unavailable, using kernel and filesystem events: " + error);
        }
    }

    private void start() {
        events.startObserving("SUBSYSTEM=usb");
        events.startObserving("SUBSYSTEM=net");
        events.startObserving("SUBSYSTEM=block");
        powerObserver.startWatching();
        observeMedia();
        Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
            @Override public void run() {
                stopping = true;
                events.stopObserving();
                powerObserver.stopWatching();
                // Serialize shutdown with any pending insertion operation.
                final CountDownLatch done = new CountDownLatch(1);
                worker.postAtFrontOfQueue(new Runnable() {
                    @Override public void run() {
                        try { runAction("shutdown"); }
                        finally { done.countDown(); }
                    }
                });
                try {
                    if (!done.await(10, TimeUnit.SECONDS))
                        System.err.println("USB Wi-Fi shutdown is waiting for an unfinished driver operation");
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                }
            }
        }, "USBWiFiShutdown"));
        System.out.println("USB Wi-Fi 0.1.7 event service ready");
        request("startup", 0);
    }

    public static void main(String[] args) throws Exception {
        Looper.prepareMainLooper();
        File jar = new File(System.getenv("CLASSPATH").split(File.pathSeparator)[0]);
        File script = new File(jar.getParentFile(), "svc/driver-event.sh");
        if (!script.isFile()) throw new IllegalStateException("Missing driver-event.sh");
        new UsbWifiMonitor(script).start();
        Looper.loop();
    }
}
