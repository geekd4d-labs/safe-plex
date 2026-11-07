package dev.geekd4dlabs.safeplex;

public final class EnforcementLatchTest {
    private static int tests;

    public static void main(String[] args) {
        EnforcementLatch latch = new EnforcementLatch(1000L);
        check("blocked startup enforces", true, latch.shouldEnforce(false, 0L));
        check("blocked repeat is rate limited", false, latch.shouldEnforce(false, 999L));
        check("blocked repeat catches relaunch", true, latch.shouldEnforce(false, 1000L));
        check("allowed state does not enforce", false, latch.shouldEnforce(true, 1100L));
        check("leaving allowed enforces immediately", true, latch.shouldEnforce(false, 1101L));
        check("clock rollback enforces fail closed", true, latch.shouldEnforce(false, 100L));
        System.out.println("EnforcementLatchTest: " + tests + " passed");
    }

    private static void check(String name, boolean expected, boolean actual) {
        tests++;
        if (expected != actual) {
            throw new AssertionError(name + ": expected " + expected + ", got " + actual);
        }
    }
}
