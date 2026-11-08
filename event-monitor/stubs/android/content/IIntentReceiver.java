// SPDX-License-Identifier: AGPL-3.0-only
package android.content;

import android.os.Binder;
import android.os.Bundle;
import android.os.IBinder;
import android.os.IInterface;

// Compile-only AOSP Android 4.4 interface signatures.
public interface IIntentReceiver extends IInterface {
    void performReceive(Intent intent, int resultCode, String data, Bundle extras,
                        boolean ordered, boolean sticky, int sendingUser);
    abstract class Stub extends Binder implements IIntentReceiver {
        public IBinder asBinder() { return this; }
    }
}
