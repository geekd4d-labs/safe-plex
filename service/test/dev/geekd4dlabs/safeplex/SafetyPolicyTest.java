package dev.geekd4dlabs.safeplex;

public final class SafetyPolicyTest {
    private static int tests;

    public static void main(String[] args) {
        unsafe("missing park", null, "0", "0.0", "0");
        unsafe("unknown park", "-", "0", "0.0", "0");
        unsafe("not in park", "0", "0", "0.0", "0");
        unsafe("moving", "1", "1", "0.0", "0");
        unsafe("speed above tolerance", "1", "0", "0.51", "0");
        unsafe("negative speed outside tolerance", "1", "0", "-0.51", "0");
        unsafe("invalid speed", "1", "0", "not-a-number", "0");
        unsafe("NaN speed", "1", "0", "NaN", "0");
        unsafe("infinite speed", "1", "0", "Infinity", "0");
        unsafe("factory restriction active", "1", "0", "0.0", "1");
        unsafe("factory restriction missing", "1", "0", "0.0", null);
        unsafe("factory restriction invalid", "1", "0", "0.0", "-");
        safe("zero speed in park", "1", "0", "0", "0");
        safe("small sensor noise", "1", "0", "0.5", "0");
        safe("small negative sensor noise", "1", "0", "-0.5", "0");
        System.out.println("SafetyPolicyTest: " + tests + " passed");
    }

    private static void safe(String name, String park, String moving, String speed, String restricted) {
        tests++;
        if (!SafetyPolicy.isSafe(park, moving, speed, restricted)) {
            throw new AssertionError(name + " should be safe");
        }
    }

    private static void unsafe(String name, String park, String moving, String speed, String restricted) {
        tests++;
        if (SafetyPolicy.isSafe(park, moving, speed, restricted)) {
            throw new AssertionError(name + " should be unsafe");
        }
    }
}
