#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APK = ROOT / "artifacts" / "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk"


class CompatibilityTestPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = ROOT / "tools" / "build_compat_test.py"
        spec = importlib.util.spec_from_file_location("build_compat_test", script)
        assert spec and spec.loader
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)

    def test_builds_deterministic_bench_only_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            first = self.builder.build(APK, out)
            first_bytes = first.read_bytes()
            second = self.builder.build(APK, out)
            self.assertEqual(first_bytes, second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [
                        "Plex-6.17.1.5294-EV6-COMPAT-TEST.apk",
                        "README-BENCH-TEST.txt",
                        "SHA256SUMS.txt",
                    ],
                )
                self.assertEqual(
                    self.builder.sha256_bytes(
                        archive.read("Plex-6.17.1.5294-EV6-COMPAT-TEST.apk")
                    ),
                    self.builder.APK_SHA256,
                )
                readme = archive.read("README-BENCH-TEST.txt").decode()
                self.assertIn("BENCH / EMULATOR ONLY", readme)
                self.assertIn("no vehicle installer", readme)
                self.assertIn("does not contain a Park Guard", readme)
                forbidden = ("NEMESIS", "HMGAPI", "mod.json", "guard")
                payload_names = "\n".join(archive.namelist())
                for name in forbidden:
                    self.assertNotIn(name, payload_names)
                for entry in archive.infolist():
                    self.assertEqual(entry.date_time, self.builder.ZIP_EPOCH)
                    self.assertEqual(entry.external_attr >> 16, 0o100644)

    def test_rejects_any_unreviewed_apk_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / "wrong.apk"
            wrong.write_bytes(b"not the reviewed Plex build")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                self.builder.build(wrong, root)


if __name__ == "__main__":
    unittest.main()
