package dev.geekd4dlabs.safeplex;

/** Exact Android package-process matching, including package:service children. */
public final class ProcessName {
    private ProcessName() {}

    public static boolean belongsToPackage(String command, String packageName) {
        return command != null
                && packageName != null
                && (command.equals(packageName) || command.startsWith(packageName + ":"));
    }
}
