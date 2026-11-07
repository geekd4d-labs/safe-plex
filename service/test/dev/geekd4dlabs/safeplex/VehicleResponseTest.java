package dev.geekd4dlabs.safeplex;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Map;

public final class VehicleResponseTest {
    private static int tests;

    public static void main(String[] args) throws Exception {
        completeResponseReturnsImmediatelyWithoutWaitingForEof();
        requestUsesExpectedProtocol();
        invalidRequestsAreRejected();
        crlfIsAccepted();
        missingReadingIsRejected();
        duplicateReadingIsRejected();
        unexpectedReadingIsRejected();
        malformedLineIsRejected();
        oversizedLineIsRejected();
        malformedValueIsRejected();
        unterminatedFinalLineIsRejected();
        System.out.println("VehicleResponseTest: " + tests + " passed");
    }

    private static void completeResponseReturnsImmediatelyWithoutWaitingForEof() throws Exception {
        byte[] data = bytes("gear.park 1\nmoving 0\nspeed 0\ndriving.restricted 0\n");
        InputStream input = new PoisonAfterDataInputStream(data);
        Map<String, String> result = VehicleResponse.read(input,
                "gear.park", "moving", "speed", "driving.restricted");
        check("park", "1", result.get("gear.park"));
        check("moving", "0", result.get("moving"));
        check("speed", "0", result.get("speed"));
        check("restricted", "0", result.get("driving.restricted"));
    }

    private static void requestUsesExpectedProtocol() throws Exception {
        check("request", "read gear.park moving speed driving.restricted\n",
                new String(VehicleResponse.request(
                        "gear.park", "moving", "speed", "driving.restricted"), "UTF-8"));
    }

    private static void invalidRequestsAreRejected() {
        requestRejected("empty request");
        requestRejected("duplicate request", "speed", "speed");
        requestRejected("invalid request", "speed\nother");
        requestRejected("overlength request", "abcdefghijklmnopqrstuvwxyz0123456789.extra");
    }

    private static void crlfIsAccepted() throws Exception {
        Map<String, String> result = VehicleResponse.read(stream("gear.park 1\r\nmoving 0\r\n"),
                "gear.park", "moving");
        check("CRLF park", "1", result.get("gear.park"));
        check("CRLF moving", "0", result.get("moving"));
    }

    private static void missingReadingIsRejected() {
        rejected("missing", stream("gear.park 1\n"), "gear.park", "moving");
    }

    private static void duplicateReadingIsRejected() {
        rejected("duplicate", stream("gear.park 1\ngear.park 1\n"), "gear.park", "moving");
    }

    private static void unexpectedReadingIsRejected() {
        rejected("unexpected", stream("gear.park 1\nother 0\n"), "gear.park", "moving");
    }

    private static void malformedLineIsRejected() {
        rejected("malformed", stream("gear.park\n"), "gear.park");
    }

    private static void oversizedLineIsRejected() {
        StringBuilder line = new StringBuilder("gear.park ");
        while (line.length() < 300) line.append('1');
        line.append('\n');
        rejected("oversized", stream(line.toString()), "gear.park");
    }

    private static void malformedValueIsRejected() {
        rejected("control value", stream("gear.park 1\u0000\n"), "gear.park");
        rejected("non-ASCII value", new ByteArrayInputStream(new byte[] {
                'g','e','a','r','.','p','a','r','k',' ',(byte) 0xc3,(byte) 0x28,'\n'}), "gear.park");
    }

    private static void unterminatedFinalLineIsRejected() {
        rejected("unterminated", stream("gear.park 1"), "gear.park");
    }

    private static void requestRejected(String name, String... readings) {
        tests++;
        try {
            VehicleResponse.request(readings);
            throw new AssertionError(name + ": request was accepted");
        } catch (IOException wanted) {
            // expected
        }
    }

    private static void rejected(String name, InputStream input, String... expected) {
        tests++;
        try {
            VehicleResponse.read(input, expected);
            throw new AssertionError(name + ": response was accepted");
        } catch (IOException wanted) {
            // expected
        }
    }

    private static InputStream stream(String text) {
        return new ByteArrayInputStream(bytes(text));
    }

    private static byte[] bytes(String text) {
        try {
            return text.getBytes("UTF-8");
        } catch (java.io.UnsupportedEncodingException impossible) {
            throw new AssertionError(impossible);
        }
    }

    private static void check(String name, String expected, String actual) {
        tests++;
        if (!expected.equals(actual)) {
            throw new AssertionError(name + ": expected " + expected + ", got " + actual);
        }
    }

    private static final class PoisonAfterDataInputStream extends InputStream {
        private final byte[] data;
        private int at;

        PoisonAfterDataInputStream(byte[] data) {
            this.data = data;
        }

        @Override
        public int read() {
            if (at >= data.length) throw new AssertionError("parser waited for EOF after complete response");
            return data[at++] & 0xff;
        }
    }
}
