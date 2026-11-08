// SPDX-License-Identifier: AGPL-3.0-only
package android.os;

// Compile-only signatures. Android supplies this hidden framework class at runtime.
public abstract class UEventObserver {
    public final void startObserving(String match) {}
    public final void stopObserving() {}
    public abstract void onUEvent(UEvent event);
    public static final class UEvent {
        public String get(String key) { return null; }
    }
}
