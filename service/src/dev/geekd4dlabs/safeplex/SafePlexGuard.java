package dev.geekd4dlabs.safeplex;

import android.os.SystemClock;
import android.util.Log;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Map;

/** Independent fail-closed supervisor for the private EV6-compatible Plex process. */
public final class SafePlexGuard {
    static final String TAG = "SafePlexGuard";
    static final String PLEX_PACKAGE = "com.plexapp.android";
    static final long POLL_MS = 200L;
    static final long SAFE_DEBOUNCE_MS = 1500L;
    static final long MAX_SAMPLE_AGE_MS = 1000L;
    static final long REPEAT_FORCE_STOP_MS = 1000L;
    static final int SCAN_CLEAR = 0;
    static final int SCAN_FOUND = 1;
    static final int SCAN_INCONCLUSIVE = 2;

    private SafePlexGuard() {}

    public static void main(String[] args) throws Exception {
        final ParkState state = new ParkState(SAFE_DEBOUNCE_MS, MAX_SAMPLE_AGE_MS);
        final EnforcementLatch latch = new EnforcementLatch(REPEAT_FORCE_STOP_MS);

        Thread enforcer = new Thread(new Runnable() {
            @Override
            public void run() {
                while (true) {
                    try {
                        long now = SystemClock.elapsedRealtime();
                        if (latch.shouldEnforce(state.isAllowed(now), now) && !enforcePlexStopped()) {
                            Log.wtf(TAG, "all Plex enforcement paths failed; retrying while blocked");
                        }
                    } catch (Throwable error) {
                        Log.wtf(TAG, "enforcer iteration failed; retrying while blocked", error);
                    }
                    sleep(POLL_MS);
                }
            }
        }, "safe-plex-enforcer");
        enforcer.setDaemon(true);
        enforcer.start();

        Log.i(TAG, "started fail-closed supervisor");
        while (true) {
            try {
                Map<String, String> values = VehicleTelemetry.read(1000,
                        "gear.park", "moving", "speed", "driving.restricted");
                boolean safe = SafetyPolicy.isSafe(
                        values.get("gear.park"),
                        values.get("moving"),
                        values.get("speed"),
                        values.get("driving.restricted"));
                state.accept(safe, SystemClock.elapsedRealtime());
            } catch (Throwable error) {
                state.accept(false, SystemClock.elapsedRealtime());
                Log.e(TAG, "vehicle telemetry unavailable; Plex remains blocked", error);
            }
            sleep(POLL_MS);
        }
    }


    static boolean enforcePlexStopped() {
        if (forceStopPlex() && waitForPlexExit(500L)) {
            Log.i(TAG, "Plex blocked: Park/speed state is unsafe, invalid, stale, or still debouncing");
            return true;
        }
        Log.e(TAG, "am force-stop failed or Plex survived; using root /proc kill fallback");
        return killPlexProcesses();
    }

    static boolean forceStopPlex() {
        Process process = null;
        try {
            process = new ProcessBuilder("/system/bin/am", "force-stop", PLEX_PACKAGE)
                    .redirectErrorStream(true)
                    .start();
            drainAsync(process.getInputStream());
            int result = ProcessDeadline.waitFor(process, 1000L);
            if (result == ProcessDeadline.TIMED_OUT) {
                Log.e(TAG, "am force-stop timed out");
                return false;
            }
            if (result != 0) {
                Log.e(TAG, "am force-stop failed with exit " + result);
                return false;
            }
            return true;
        } catch (Throwable error) {
            Log.e(TAG, "cannot force-stop Plex", error);
            return false;
        } finally {
            if (process != null) {
                process.destroy();
            }
        }
    }

    static void drainAsync(final InputStream input) {
        Thread drainer = new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    drain(input);
                } catch (IOException error) {
                    Log.w(TAG, "force-stop output drain failed", error);
                }
            }
        }, "plex-force-stop-output");
        drainer.setDaemon(true);
        drainer.start();
    }

    static boolean killPlexProcesses() {
        int result = scanPlexProcesses(true);
        if (result == SCAN_INCONCLUSIVE) {
            return false;
        }
        return waitForPlexExit(500L);
    }

    static boolean waitForPlexExit(long timeoutMs) {
        long deadline = SystemClock.elapsedRealtime() + timeoutMs;
        while (true) {
            int result = scanPlexProcesses(false);
            if (result == SCAN_CLEAR) {
                return true;
            }
            if (result == SCAN_INCONCLUSIVE || SystemClock.elapsedRealtime() >= deadline) {
                return false;
            }
            sleep(50L);
        }
    }

    static int scanPlexProcesses(boolean kill) {
        File[] entries = new File("/proc").listFiles();
        if (entries == null) {
            Log.e(TAG, "cannot scan /proc for Plex processes");
            return SCAN_INCONCLUSIVE;
        }
        boolean found = false;
        boolean conclusive = true;
        for (File entry : entries) {
            int pid;
            try {
                pid = Integer.parseInt(entry.getName());
            } catch (NumberFormatException notPid) {
                continue;
            }
            String command;
            try {
                command = readCommand(new File(entry, "cmdline"));
            } catch (IOException unreadable) {
                // A process that vanished between listFiles() and open() is already gone.
                // Any still-existing unreadable PID makes the safety scan inconclusive.
                if (entry.exists()) {
                    conclusive = false;
                    Log.e(TAG, "cannot inspect live process " + pid, unreadable);
                }
                continue;
            }
            if (!ProcessName.belongsToPackage(command, PLEX_PACKAGE)) {
                continue;
            }
            found = true;
            if (!kill) {
                continue;
            }
            try {
                android.os.Process.killProcess(pid);
                Log.w(TAG, "killed Plex process " + pid + " through root fallback");
            } catch (Throwable error) {
                conclusive = false;
                Log.e(TAG, "cannot kill Plex process " + pid, error);
            }
        }
        if (!conclusive) {
            return SCAN_INCONCLUSIVE;
        }
        return found ? SCAN_FOUND : SCAN_CLEAR;
    }

    static String readCommand(File path) throws IOException {
        FileInputStream input = new FileInputStream(path);
        try {
            byte[] bytes = new byte[512];
            int count = input.read(bytes);
            if (count <= 0) {
                return "";
            }
            int end = 0;
            while (end < count && bytes[end] != 0) {
                end++;
            }
            return new String(bytes, 0, end, "UTF-8");
        } finally {
            input.close();
        }
    }

    static void drain(InputStream input) throws IOException {
        byte[] buffer = new byte[1024];
        while (input.read(buffer) >= 0) {
            // Prevent am output from filling its pipe.
        }
        input.close();
    }

    static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException interrupted) {
            Log.w(TAG, "guard sleep interrupted; continuing fail-closed", interrupted);
        }
    }
}
