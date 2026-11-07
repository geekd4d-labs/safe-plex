package dev.geekd4dlabs.safeplex;

public final class ProcessNameTest {
    private static int tests;

    public static void main(String[] args) {
        check("main Plex process", true, ProcessName.belongsToPackage("com.plexapp.android", "com.plexapp.android"));
        check("Plex child process", true, ProcessName.belongsToPackage("com.plexapp.android:media", "com.plexapp.android"));
        check("lookalike package", false, ProcessName.belongsToPackage("com.plexapp.android.fake", "com.plexapp.android"));
        check("prefix package", false, ProcessName.belongsToPackage("com.plexapp", "com.plexapp.android"));
        check("empty command", false, ProcessName.belongsToPackage("", "com.plexapp.android"));
        check("missing command", false, ProcessName.belongsToPackage(null, "com.plexapp.android"));
        System.out.println("ProcessNameTest: " + tests + " passed");
    }

    private static void check(String name, boolean expected, boolean actual) {
        tests++;
        if (expected != actual) throw new AssertionError(name + ": expected " + expected + ", got " + actual);
    }
}
