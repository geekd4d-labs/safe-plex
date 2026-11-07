package dev.geekd4dlabs.safeplex;

import java.io.File;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Fail-closed factory vehicle telemetry for the standalone build.
 *
 * <p>Reads the same four readings the guard policy consumes — {@code gear.park},
 * {@code moving}, {@code speed}, {@code driving.restricted} — but from the head
 * unit's own binder services (the same ones the EV6 Plex video gate uses), with
 * no HMG-API dependency.
 *
 * <p>Fail-closed by construction: a reading that cannot be obtained is reported
 * as {@code "-"} (car did not respond). The policy treats any such reading as
 * blocked. Values are never inferred or defaulted toward safe.
 *
 * <p>Every Android reference goes through reflection so this class stays
 * host-compilable (no android.jar) and host-testable; the live path mirrors the
 * validated EV6 video gate (framework jars, ServiceManager, asInterface).
 */
public final class FactoryVehicleTelemetry {
    public static final String AUTOMOTIVE_JAR = "/system/framework/automotive.jar";
    public static final String HCAN_JAR = "/system/framework/com.hkmc.ext.hcan.jar";
    public static final String SERVICE_MANAGER = "android.os.ServiceManager";
    public static final String IBINDER = "android.os.IBinder";
    public static final String PATH_CLASS_LOADER = "dalvik.system.PathClassLoader";
    static final String NO_RESPONSE = "-";

    private FactoryVehicleTelemetry() {
    }

    /**
     * Seam for the live binder reads. {@link #read(LiveServices)} is pure given
     * these readings; the head-unit implementation is {@link #liveServices()}.
     */
    public static interface LiveServices {
        Integer gearP() throws Exception;

        Float speed() throws Exception;

        Boolean moving() throws Exception;

        Integer drivingRestricted() throws Exception;
    }

    /**
     * Maps raw readings to the policy format. A null reading (unavailable)
     * becomes {@code "-"}; a present reading is reported verbatim.
     */
    static Map<String, String> readings(Integer gearP, Float speed, Boolean moving,
                                        Integer drivingRestricted) {
        Map<String, String> values = new LinkedHashMap<String, String>();
        values.put("gear.park", gearP == null ? NO_RESPONSE : (gearP == 1 ? "1" : "0"));
        values.put("moving", moving == null ? NO_RESPONSE : (moving ? "1" : "0"));
        values.put("speed", speed == null ? NO_RESPONSE : String.valueOf(speed));
        values.put("driving.restricted",
                drivingRestricted == null ? NO_RESPONSE : String.valueOf(drivingRestricted));
        return values;
    }

    /**
     * One full poll against the live head-unit services.
     */
    public static Map<String, String> read() {
        LiveServices services = null;
        try {
            services = liveServices();
        } catch (Throwable unavailable) {
            invalidateServices();
        }
        Map<String, String> values = read(services);
        if (values.containsValue(NO_RESPONSE)) {
            // Something the cache promised did not answer: drop it so the next
            // poll rebinds from scratch instead of trusting a stale proxy.
            invalidateServices();
        }
        return values;
    }

    /**
     * Pure fail-closed mapping given a read source (null source: all readings
     * unanswered). Each reading fails independently; no reading is fabricated.
     */
    static Map<String, String> read(LiveServices services) {
        Integer gearP = null;
        Float speed = null;
        Boolean moving = null;
        Integer drivingRestricted = null;
        if (services != null) {
            try {
                gearP = services.gearP();
            } catch (Throwable unavailable) {
                // Unanswered reading; stays "-".
            }
            try {
                speed = services.speed();
            } catch (Throwable unavailable) {
                // Unanswered reading; stays "-".
            }
            try {
                moving = services.moving();
            } catch (Throwable unavailable) {
                // Unanswered reading; stays "-".
            }
            try {
                drivingRestricted = services.drivingRestricted();
            } catch (Throwable unavailable) {
                // Unanswered reading; stays "-".
            }
        }
        return readings(gearP, speed, moving, drivingRestricted);
    }

    private static final Object LOCK = new Object();
    private static volatile LiveServices services;

    static LiveServices liveServices() throws Exception {
        LiveServices current = services;
        if (current != null) {
            return current;
        }
        synchronized (LOCK) {
            if (services == null) {
                services = new FactoryServices();
            }
            return services;
        }
    }

    static void invalidateServices() {
        synchronized (LOCK) {
            services = null;
        }
    }

    /** Live binder implementation for the EV6 head unit (reflection-only). */
    private static final class FactoryServices implements LiveServices {
        private final ClassLoader automotive;
        private final ClassLoader hscan;
        private final Object system;
        private final Object hscanService;
        private final Object regulation;

        FactoryServices() throws Exception {
            automotive = loadJar(AUTOMOTIVE_JAR, FactoryVehicleTelemetry.class.getClassLoader());
            hscan = loadJar(HCAN_JAR, automotive);
            system = service(automotive, "com.hkmc.Service", "SYSTEM_SERVICE",
                    "com.hkmc.micom.ISystemService");
            hscanService = service(hscan,
                    "com.hkmc.telematics.hscan.tm_interface.TM_HSCANAdapter",
                    "TM_HSCAN_SERVICE",
                    "com.hkmc.telematics.hscan.tm_interface.ITM_HSCANService");
            regulation = service(automotive, "com.hkmc.Service", "REGULATION_SERVICE",
                    "com.hkmc.regulation.IRegulationManager");
        }

        private static ClassLoader loadJar(String path, ClassLoader parent) throws Exception {
            if (!new File(path).canRead()) {
                throw new IllegalStateException("vehicle framework missing: " + path);
            }
            return (ClassLoader) Class.forName(PATH_CLASS_LOADER)
                    .getConstructor(String.class, ClassLoader.class)
                    .newInstance(path, parent);
        }

        private static Object service(ClassLoader loader, String constantsClass,
                                      String fieldName, String apiClass) throws Exception {
            String name = (String) loader.loadClass(constantsClass)
                    .getField(fieldName)
                    .get(null);
            Class<?> binderClass = Class.forName(IBINDER);
            Object binder = Class.forName(SERVICE_MANAGER)
                    .getMethod("getService", String.class)
                    .invoke(null, name);
            if (binder == null) {
                throw new IllegalStateException("vehicle service unavailable: " + name);
            }
            if (!(Boolean) binderClass.getMethod("isBinderAlive").invoke(binder)) {
                throw new IllegalStateException("vehicle service dead: " + name);
            }
            return loader.loadClass(apiClass + "$Stub")
                    .getMethod("asInterface", binderClass)
                    .invoke(null, binder);
        }

        @Override
        public Integer gearP() throws Exception {
            return (Integer) automotive.loadClass("com.hkmc.micom.ISystemService")
                    .getMethod("getGearPStatus")
                    .invoke(system);
        }

        @Override
        public Float speed() throws Exception {
            return (Float) hscan.loadClass(
                            "com.hkmc.telematics.hscan.tm_interface.ITM_HSCANService")
                    .getMethod("getCarSpeed", byte.class)
                    .invoke(hscanService, (byte) 0);
        }

        @Override
        public Boolean moving() throws Exception {
            return (Boolean) hscan.loadClass(
                            "com.hkmc.telematics.hscan.tm_interface.ITM_HSCANService")
                    .getMethod("IsCarMoving")
                    .invoke(hscanService);
        }

        @Override
        public Integer drivingRestricted() throws Exception {
            return (Integer) automotive.loadClass("com.hkmc.regulation.IRegulationManager")
                    .getMethod("getStatus")
                    .invoke(regulation);
        }
    }
}
