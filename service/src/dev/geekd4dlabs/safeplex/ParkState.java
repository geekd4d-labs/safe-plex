package dev.geekd4dlabs.safeplex;

/** Tracks safe-state debounce and telemetry freshness without trusting wall-clock time. */
public final class ParkState {
    private final long safeDebounceMs;
    private final long maxSampleAgeMs;
    private long safeSinceMs = -1L;
    private long lastSampleMs = -1L;
    private boolean latestSafe;

    public ParkState(long safeDebounceMs, long maxSampleAgeMs) {
        if (safeDebounceMs < 0L || maxSampleAgeMs <= 0L) {
            throw new IllegalArgumentException("invalid timing");
        }
        this.safeDebounceMs = safeDebounceMs;
        this.maxSampleAgeMs = maxSampleAgeMs;
    }

    public synchronized void accept(boolean safe, long nowMs) {
        boolean previousFresh = latestSafe
                && lastSampleMs >= 0L
                && nowMs >= lastSampleMs
                && nowMs - lastSampleMs <= maxSampleAgeMs;
        if (!safe) {
            latestSafe = false;
            safeSinceMs = -1L;
            lastSampleMs = nowMs;
            return;
        }
        if (!previousFresh) {
            safeSinceMs = nowMs;
        }
        latestSafe = true;
        lastSampleMs = nowMs;
    }

    public synchronized boolean isAllowed(long nowMs) {
        return latestSafe
                && safeSinceMs >= 0L
                && lastSampleMs >= 0L
                && nowMs >= lastSampleMs
                && nowMs - lastSampleMs <= maxSampleAgeMs
                && nowMs - safeSinceMs >= safeDebounceMs;
    }
}
