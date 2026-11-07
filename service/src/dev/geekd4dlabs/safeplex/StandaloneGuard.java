package dev.geekd4dlabs.safeplex;

import android.os.SystemClock;
import android.util.Log;

import java.util.Map;

/**
 * Fail-closed supervisor for the standalone (NEMESIS) build.
 *
 * <p>Same policy, same enforcement, same fail-closed behaviour as
 * {@link SafePlexGuard} (the HMG build): one shared {@link ParkState}, one
 * shared {@link EnforcementLatch}, and every enforcement path runs through
 * {@link SafePlexGuard#enforcePlexStopped()}. The only difference is the
 * telemetry source: the head unit's own binder services, no HMG-API.
 */
public final class StandaloneGuard {
    static final String TAG = "StandaloneGuard";
    private static final String STALE_LOG =
            "vehicle telemetry unavailable; Plex remains blocked";

    private StandaloneGuard() {
    }

    public static void main(String[] args) throws Exception {
        final ParkState state =
                new ParkState(SafePlexGuard.SAFE_DEBOUNCE_MS, SafePlexGuard.MAX_SAMPLE_AGE_MS);
        final EnforcementLatch latch =
                new EnforcementLatch(SafePlexGuard.REPEAT_FORCE_STOP_MS);

        Thread enforcer = new Thread(new Runnable() {
            @Override
            public void run() {
                while (true) {
                    try {
                        long now = SystemClock.elapsedRealtime();
                        if (latch.shouldEnforce(state.isAllowed(now), now)
                                && !SafePlexGuard.enforcePlexStopped()) {
                            Log.wtf(TAG, "all Plex enforcement paths failed; retrying while blocked");
                        }
                    } catch (Throwable error) {
                        Log.wtf(TAG, "enforcer iteration failed; retrying while blocked", error);
                    }
                    SafePlexGuard.sleep(SafePlexGuard.POLL_MS);
                }
            }
        }, "safe-plex-standalone-enforcer");
        enforcer.setDaemon(true);
        enforcer.start();

        Log.i(TAG, "started fail-closed supervisor (standalone; factory vehicle telemetry)");
        while (true) {
            try {
                Map<String, String> values = FactoryVehicleTelemetry.read();
                boolean safe = SafetyPolicy.isSafe(
                        values.get("gear.park"),
                        values.get("moving"),
                        values.get("speed"),
                        values.get("driving.restricted"));
                state.accept(safe, SystemClock.elapsedRealtime());
            } catch (Throwable error) {
                state.accept(false, SystemClock.elapsedRealtime());
                Log.e(TAG, STALE_LOG, error);
            }
            SafePlexGuard.sleep(SafePlexGuard.POLL_MS);
        }
    }
}
