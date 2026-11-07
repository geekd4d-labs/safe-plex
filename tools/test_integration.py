#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IntegrationContractTest(unittest.TestCase):
    def test_mod_owns_plex_and_declares_both_safety_layers(self):
        mod = json.loads((ROOT / "mod" / "mod.json").read_text())
        self.assertEqual(mod["id"], "geekd4dlabs-safe-plex")
        self.assertEqual(mod["name"], "SAFE PLEX")
        self.assertEqual(mod["version"], "0.1.0")
        self.assertEqual(mod["hmgapi"], "1.0.2")
        self.assertIn("PARKED", mod["description"])
        self.assertIn("illegal", mod["description"])
        self.assertIn("reckless", mod["description"])
        self.assertEqual(
            mod["apps"],
            [{"apk": "app/Plex.apk", "package": "com.plexapp.android"}],
        )
        self.assertEqual(mod["not_while_driving"], ["com.plexapp.android"])
        self.assertEqual(
            mod["vehicle"]["read"],
            ["gear.park", "moving", "speed", "driving.restricted"],
        )
        service = mod["services"][0]
        launcher = mod["provides"]["launcher"][0]
        self.assertEqual(launcher["title"], "SAFE PLEX")
        self.assertEqual(launcher["package"], "com.plexapp.android")
        self.assertEqual(launcher["class"], "com.plexapp.plex.activities.SplashActivity")
        self.assertEqual(service["name"], "safe-plex-guard")
        self.assertEqual(service["jar"], "svc/safe-plex-guard.jar")
        self.assertEqual(service["class"], "dev.geekd4dlabs.safeplex.SafePlexGuard")
        self.assertEqual(service["user"], "root")
        self.assertEqual(service["start"], "android")
        self.assertTrue(service["restart"])
        self.assertEqual(
            mod["system"],
            [{"model": ["CVEV"], "region": "USA", "firmware": "260507"}],
        )

    def test_guard_is_fail_closed_and_force_stops_plex(self):
        source = (ROOT / "service/src/dev/geekd4dlabs/safeplex/SafePlexGuard.java").read_text()
        telemetry = (ROOT / "service/src/dev/geekd4dlabs/safeplex/VehicleTelemetry.java").read_text()
        self.assertIn('PLEX_PACKAGE = "com.plexapp.android"', source)
        self.assertIn('VehicleTelemetry.read(1000', source)
        self.assertIn('SOCKET = "hmgapi-vehicle"', telemetry)
        self.assertIn('LocalSocketAddress.Namespace.ABSTRACT', telemetry)
        self.assertIn('VehicleResponse.read', telemetry)
        self.assertLess(telemetry.index('socket.connect('), telemetry.index('socket.setSoTimeout('))
        self.assertIn('values.get("driving.restricted")', source)
        self.assertIn('state.accept(false', source)
        self.assertIn('"/system/bin/am", "force-stop", PLEX_PACKAGE', source)
        self.assertIn('ProcessDeadline.waitFor(process, 1000L)', source)
        self.assertIn('return killPlexProcesses()', source)
        self.assertIn('new File("/proc").listFiles()', source)
        self.assertIn('waitForPlexExit(500L)', source)
        self.assertIn('SCAN_INCONCLUSIVE', source)
        self.assertIn('if (entry.exists())', source)
        self.assertIn('state.accept(safe, SystemClock.elapsedRealtime())', source)
        self.assertIn('enforcer iteration failed; retrying while blocked', source)
        self.assertIn('guard sleep interrupted; continuing fail-closed', source)
        self.assertNotIn('com.hkmc.intent.action.TOAST', source)
        self.assertNotIn('showWarningNotice', source)


if __name__ == "__main__":
    unittest.main()
