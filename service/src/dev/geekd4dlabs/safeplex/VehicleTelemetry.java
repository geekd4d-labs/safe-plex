package dev.geekd4dlabs.safeplex;

import android.net.LocalSocket;
import android.net.LocalSocketAddress;

import java.io.OutputStream;
import java.util.Map;

/** Reads complete telemetry directly from HMG's root-only vehicle service. */
public final class VehicleTelemetry {
    static final String SOCKET = "hmgapi-vehicle";

    private VehicleTelemetry() {}

    public static Map<String, String> read(int timeoutMs, String... names) throws Exception {
        LocalSocket socket = new LocalSocket();
        try {
            socket.connect(new LocalSocketAddress(SOCKET, LocalSocketAddress.Namespace.ABSTRACT));
            socket.setSoTimeout(timeoutMs);
            OutputStream output = socket.getOutputStream();
            output.write(VehicleResponse.request(names));
            output.flush();
            // HMG-API 1.0.2's public hmgapid vehicle operation waits for socket EOF and
            // times out after three seconds on this unit. The internal vehicle service
            // returns every requested line immediately, so stop as soon as all exact
            // declared readings arrive instead of waiting for EOF.
            return VehicleResponse.read(socket.getInputStream(), names);
        } finally {
            socket.close();
        }
    }
}
