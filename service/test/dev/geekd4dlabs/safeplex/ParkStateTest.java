package dev.geekd4dlabs.safeplex;

public final class ParkStateTest {
    private static int tests;

    public static void main(String[] args) {
        ParkState state = new ParkState(1500L, 1000L);
        check("starts blocked", false, state.isAllowed(0L));

        state.accept(true, 100L);
        state.accept(true, 1000L);
        check("safe sample is debounced", false, state.isAllowed(1599L));
        state.accept(true, 1600L);
        check("stable safe becomes allowed", true, state.isAllowed(1600L));
        check("safe sample becomes stale", false, state.isAllowed(2601L));

        state.accept(true, 3000L);
        state.accept(true, 3800L);
        check("must debounce again after stale", false, state.isAllowed(4000L));
        state.accept(true, 4300L);
        check("continued safe reaches debounce", true, state.isAllowed(4500L));

        state.accept(false, 4501L);
        check("unsafe sample blocks immediately", false, state.isAllowed(4501L));
        state.accept(true, 5000L);
        state.accept(true, 6000L);
        check("safe debounce restarts after unsafe", false, state.isAllowed(6499L));
        state.accept(true, 6500L);
        check("safe debounce completes again", true, state.isAllowed(6500L));

        System.out.println("ParkStateTest: " + tests + " passed");
    }

    private static void check(String name, boolean expected, boolean actual) {
        tests++;
        if (expected != actual) {
            throw new AssertionError(name + ": expected " + expected + ", got " + actual);
        }
    }
}
