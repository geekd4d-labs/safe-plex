package dev.geekd4dlabs.safeplex;

/** Decides when to repeat force-stop while blocked so direct relaunches are caught. */
public final class EnforcementLatch {
    private final long repeatMs;
    private boolean previouslyAllowed = true;
    private long lastEnforcedMs = -1L;

    public EnforcementLatch(long repeatMs) {
        if (repeatMs <= 0L) {
            throw new IllegalArgumentException("repeatMs must be positive");
        }
        this.repeatMs = repeatMs;
    }

    public synchronized boolean shouldEnforce(boolean allowed, long nowMs) {
        if (allowed) {
            previouslyAllowed = true;
            return false;
        }
        boolean transitioned = previouslyAllowed;
        boolean clockRollback = lastEnforcedMs >= 0L && nowMs < lastEnforcedMs;
        boolean repeatDue = lastEnforcedMs < 0L || nowMs - lastEnforcedMs >= repeatMs;
        previouslyAllowed = false;
        if (transitioned || clockRollback || repeatDue) {
            lastEnforcedMs = nowMs;
            return true;
        }
        return false;
    }
}
