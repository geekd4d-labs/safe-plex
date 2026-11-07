package dev.geekd4dlabs.safeplex;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Parses one complete HMG vehicle-service response without waiting for socket EOF. */
public final class VehicleResponse {
    static final int MAX_LINE_BYTES = 256;

    private VehicleResponse() {}

    public static byte[] request(String... names) throws IOException {
        StringBuilder request = new StringBuilder("read");
        Set<String> seen = new LinkedHashSet<String>();
        for (String name : names) {
            if (!validName(name) || !seen.add(name)) {
                throw new IOException("invalid vehicle reading request");
            }
            request.append(' ').append(name);
        }
        if (seen.isEmpty()) throw new IOException("empty vehicle reading request");
        request.append('\n');
        return request.toString().getBytes("UTF-8");
    }

    public static Map<String, String> read(InputStream input, String... expectedNames) throws IOException {
        Set<String> expected = new LinkedHashSet<String>();
        for (String name : expectedNames) {
            if (!validName(name) || !expected.add(name)) {
                throw new IllegalArgumentException("invalid expected vehicle reading");
            }
        }
        Map<String, String> values = new LinkedHashMap<String, String>();
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        while (values.size() < expected.size()) {
            int next = input.read();
            if (next < 0) {
                throw new IOException("vehicle response ended before all readings arrived");
            }
            if (next == '\n') {
                accept(line.toByteArray(), expected, values);
                line.reset();
                continue;
            }
            if (line.size() >= MAX_LINE_BYTES) {
                throw new IOException("vehicle response line is too long");
            }
            line.write(next);
        }
        return values;
    }

    private static boolean validName(String name) {
        if (name == null || name.length() == 0 || name.length() > 40) return false;
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' || c == '_')) {
                return false;
            }
        }
        return true;
    }

    private static void accept(byte[] bytes, Set<String> expected, Map<String, String> values)
            throws IOException {
        int length = bytes.length;
        if (length > 0 && bytes[length - 1] == '\r') length--;
        String line = new String(bytes, 0, length, "UTF-8");
        int separator = line.indexOf(' ');
        if (separator <= 0 || separator == line.length() - 1) {
            throw new IOException("malformed vehicle response line");
        }
        String name = line.substring(0, separator);
        String value = line.substring(separator + 1);
        if (!expected.contains(name)) {
            throw new IOException("unexpected vehicle reading: " + name);
        }
        if (values.containsKey(name)) {
            throw new IOException("duplicate vehicle reading: " + name);
        }
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c < 0x21 || c > 0x7e) {
                throw new IOException("malformed vehicle value: " + name);
            }
        }
        values.put(name, value);
    }
}
