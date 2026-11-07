package dev.geekd4dlabs.safeplex;

import java.util.Map;

public final class FactoryVehicleTelemetryTest {
    private static int tests;

    public static void main(String[] args) {
        Map<String, String> parked = read(1, 0.0f, false, 0);
        tests++;
        if (!"1".equals(parked.get("gear.park")) || !"0".equals(parked.get("moving"))
                || !"0.0".equals(parked.get("speed")) || !"0".equals(parked.get("driving.restricted"))) {
            throw new AssertionError("policy encoding must be 0/1 strings, got " + parked);
        }
        safe("confirmed parked", parked);
        safe("slow roll below half km/h", read(1, 0.4f, false, 0));
        blocked("missing gear", read(null, 0.0f, false, 0), "gear.park", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("missing speed", read(1, null, false, 0), "speed", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("missing moving", read(1, 0.0f, null, 0), "moving", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("missing restriction", read(1, 0.0f, false, null), "driving.restricted", FactoryVehicleTelemetry.NO_RESPONSE);
        Map<String, String> dead = FactoryVehicleTelemetry.read(null);
        blocked("total service failure", dead, "gear.park", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("total service failure: moving", dead, "moving", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("total service failure: speed", dead, "speed", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("total service failure: restricted", dead, "driving.restricted", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("one binder dies mid-poll", readThrowingSpeed(), "speed", FactoryVehicleTelemetry.NO_RESPONSE);
        blocked("non-park gear", read(2, 0.0f, false, 0), "gear.park", "0");
        blocked("moving car", read(1, 0.0f, true, 0), "moving", "1");
        blocked("driving restriction", read(1, 0.0f, false, 1), "driving.restricted", "1");
        blocked("speed above tolerance", read(1, 0.6f, false, 0), "speed", "0.6");
        System.out.println("FactoryVehicleTelemetryTest: " + tests + " passed");
    }

    private static Map<String, String> read(Integer gearP, Float speed, Boolean moving,
                                            Integer restricted) {
        return FactoryVehicleTelemetry.read(new FactoryVehicleTelemetry.LiveServices() {
            @Override
            public Integer gearP() {
                return gearP;
            }

            @Override
            public Float speed() {
                return speed;
            }

            @Override
            public Boolean moving() {
                return moving;
            }

            @Override
            public Integer drivingRestricted() {
                return restricted;
            }
        });
    }

    private static Map<String, String> readThrowingSpeed() {
        return FactoryVehicleTelemetry.read(new FactoryVehicleTelemetry.LiveServices() {
            @Override
            public Integer gearP() {
                return 1;
            }

            @Override
            public Float speed() throws Exception {
                throw new IllegalStateException("binder died");
            }

            @Override
            public Boolean moving() {
                return false;
            }

            @Override
            public Integer drivingRestricted() {
                return 0;
            }
        });
    }

    private static void safe(String name, Map<String, String> values) {
        tests++;
        if (!SafetyPolicy.isSafe(values.get("gear.park"), values.get("moving"),
                values.get("speed"), values.get("driving.restricted"))) {
            throw new AssertionError(name + " should be safe");
        }
    }

    private static void blocked(String name, Map<String, String> values, String key, String expected) {
        tests++;
        if (!expected.equals(values.get(key))) {
            throw new AssertionError(name + ": " + key + " should be \"" + expected
                    + "\", got \"" + values.get(key) + "\"");
        }
        if (SafetyPolicy.isSafe(values.get("gear.park"), values.get("moving"),
                values.get("speed"), values.get("driving.restricted"))) {
            throw new AssertionError(name + " should be blocked");
        }
    }
}
