#!/usr/bin/env python3
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackagingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = ROOT / "tools" / "build_mod.py"
        spec = importlib.util.spec_from_file_location("build_mod", script)
        assert spec and spec.loader
        cls.packager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.packager)

    def test_established_hmg_author_identity_is_pinned(self):
        self.assertEqual(
            self.packager.HMG_AUTHOR_UUID,
            "96f22dc5-6d6e-8098-bbc9-e554834eb78d",
        )

    def test_usb_packaging_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod = root / "mod.zip"
            with zipfile.ZipFile(mod, "w") as archive:
                archive.writestr("mod.json", json.dumps({"id": "test"}))
            first = root / "first.zip"
            second = root / "second.zip"
            self.packager.write_usb(mod, first, "test instructions")
            self.packager.write_usb(mod, second, "test instructions")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                for entry in archive.infolist():
                    self.assertEqual(entry.date_time, self.packager.ZIP_EPOCH)
                    self.assertEqual(entry.external_attr >> 16, 0o100644)

    def test_usb_recursively_preserves_mod_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod = root / "mod.zip"
            with zipfile.ZipFile(mod, "w") as archive:
                archive.writestr("mod.json", json.dumps({"id": "test"}))
                archive.writestr("META-HMGAPI/signature", b"signed-fixture")
            usb = root / "usb.zip"
            self.packager.write_usb(mod, usb, "test instructions")
            self.packager.verify_usb(mod, usb)
            with zipfile.ZipFile(usb) as archive:
                self.assertEqual(archive.read("HMGAPI/updates/mod.zip"), mod.read_bytes())

    def test_usb_verifier_rejects_corrupt_nested_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod = root / "mod.zip"
            with zipfile.ZipFile(mod, "w") as archive:
                archive.writestr("mod.json", "{}")
            usb = root / "usb.zip"
            with zipfile.ZipFile(usb, "w") as archive:
                archive.writestr("HMGAPI/updates/mod.zip", b"corrupt")
            with self.assertRaises(ValueError):
                self.packager.verify_usb(mod, usb)


if __name__ == "__main__":
    unittest.main()
