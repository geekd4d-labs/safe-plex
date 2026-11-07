package dev.geekd4dlabs.safeplex;

/** Pure fail-closed decision logic for vehicle telemetry. */
public final class SafetyPolicy {
    public static final double MAX_STATIONARY_SPEED_KMH = 0.5d;

    private SafetyPolicy() {}

    public static boolean isSafe(String park, String moving, String speedText, String restricted) {
        if (!"1".equals(park)
                || !"0".equals(moving)
                || !"0".equals(restricted)
                || speedText == null) {
            return false;
        }
        try {
            double speed = Double.parseDouble(speedText);
            return !Double.isNaN(speed)
                    && !Double.isInfinite(speed)
                    && Math.abs(speed) <= MAX_STATIONARY_SPEED_KMH;
        } catch (NumberFormatException ignored) {
            return false;
        }
    }
}
