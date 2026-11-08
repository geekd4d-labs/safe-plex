#!/usr/bin/env python3
import importlib.util
import configparser
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "nemesis-test"


class CompatNemesisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = ROOT / "tools" / "build_compat_nemesis.py"
        spec = importlib.util.spec_from_file_location("build_compat_nemesis", script)
        assert spec and spec.loader
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)

    def test_profile_is_separate_guarded_nemesis_package(self):
        parser = configparser.ConfigParser(strict=True)
        parser.read_string((PROFILE / "src" / "NEMESIS.data").read_text())
        self.assertEqual(parser.get("nemesis", "id"), "plex.geekd4dlabs.compat-test")
        self.assertEqual(parser.get("nemesis", "name"), "PLEX COMPAT TEST (GUARDED)")
        self.assertEqual(parser.get("nemesis", "types"), "application,service")
        self.assertEqual(parser.get("nemesis", "package-version"), "0.1.2")
        self.assertLessEqual(len(parser.get("nemesis", "short-desc")), 64)
        self.assertEqual(parser.get("app.0", "package"), "com.plexapp.android")
        self.assertEqual(parser.get("service.0", "name"), "plex-compat-test-guard")
        self.assertEqual(parser.get("service.0", "uid"), "root")
        self.assertEqual(
            parser.get("app.0", "component"),
            "com.plexapp.android/com.plexapp.plex.activities.SplashActivity",
        )

    def test_apk_profile_is_fullscreen_compatibility_build(self):
        self.assertEqual(
            self.builder.PLEX_SHA256,
            "d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f",
        )
        self.assertEqual(self.builder.NEMESIS_ID, "plex.geekd4dlabs.compat-test")
        self.assertEqual(
            self.builder.DEFAULT_APK.name,
            "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk",
        )
        readme = (PROFILE / "README-PRIVATE-TEST.txt").read_text()
        self.assertIn("GET_TASKS", readme)
        self.assertIn("CA bundle", readme)
        self.assertIn("includes the fullscreen patch", readme)
        self.assertIn("Park Guard remains mandatory", readme)

    def test_usb_descriptor_targets_only_the_separate_package(self):
        parser = configparser.ConfigParser(strict=True)
        parser.read_string((PROFILE / "src" / "USB-NEMESIS.data").read_text())
        self.assertEqual(parser.get("nemesis", "type"), "install")
        self.assertEqual(
            parser.get("nemesis", "path"),
            "Packages/plex.geekd4dlabs.compat-test.zip",
        )


if __name__ == "__main__":
    unittest.main()
