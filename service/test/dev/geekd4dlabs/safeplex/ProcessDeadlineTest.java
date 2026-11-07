package dev.geekd4dlabs.safeplex;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

public final class ProcessDeadlineTest {
    private static int tests;

    public static void main(String[] args) throws Exception {
        FakeProcess complete = new FakeProcess(true, 0);
        check("completed process returns exit", 0, ProcessDeadline.waitFor(complete, 20L));
        check("completed process is not destroyed", false, complete.destroyed);

        FakeProcess hung = new FakeProcess(false, 0);
        check("hung process reports timeout", ProcessDeadline.TIMED_OUT, ProcessDeadline.waitFor(hung, 20L));
        check("hung process is destroyed", true, hung.destroyed);
        System.out.println("ProcessDeadlineTest: " + tests + " passed");
    }

    private static void check(String name, int expected, int actual) {
        tests++;
        if (expected != actual) throw new AssertionError(name + ": expected " + expected + ", got " + actual);
    }

    private static void check(String name, boolean expected, boolean actual) {
        tests++;
        if (expected != actual) throw new AssertionError(name + ": expected " + expected + ", got " + actual);
    }

    private static final class FakeProcess extends Process {
        private final boolean initiallyComplete;
        private final int result;
        boolean destroyed;

        FakeProcess(boolean initiallyComplete, int result) {
            this.initiallyComplete = initiallyComplete;
            this.result = result;
        }

        @Override public OutputStream getOutputStream() { return new ByteArrayOutputStream(); }
        @Override public InputStream getInputStream() { return new ByteArrayInputStream(new byte[0]); }
        @Override public InputStream getErrorStream() { return new ByteArrayInputStream(new byte[0]); }
        @Override public int waitFor() { return result; }
        @Override public int exitValue() {
            if (!initiallyComplete && !destroyed) throw new IllegalThreadStateException("still running");
            return result;
        }
        @Override public void destroy() { destroyed = true; }
    }
}
