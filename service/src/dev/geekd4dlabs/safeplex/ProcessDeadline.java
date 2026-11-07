package dev.geekd4dlabs.safeplex;

/** API-19-compatible bounded wait for a child process. */
public final class ProcessDeadline {
    public static final int TIMED_OUT = Integer.MIN_VALUE;

    private ProcessDeadline() {}

    public static int waitFor(Process process, long timeoutMs) throws InterruptedException {
        if (timeoutMs <= 0L) {
            throw new IllegalArgumentException("timeoutMs must be positive");
        }
        final long started = System.nanoTime();
        final long timeoutNanos = timeoutMs * 1000000L;
        while (true) {
            try {
                return process.exitValue();
            } catch (IllegalThreadStateException stillRunning) {
                if (System.nanoTime() - started >= timeoutNanos) {
                    process.destroy();
                    return TIMED_OUT;
                }
                try {
                    Thread.sleep(10L);
                } catch (InterruptedException interrupted) {
                    process.destroy();
                    throw interrupted;
                }
            }
        }
    }
}
