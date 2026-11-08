#!/usr/bin/env python3
"""Build the guarded Plex compatibility NEMESIS test package."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "nemesis-test"
NEMESIS_ID = "plex.geekd4dlabs.compat-test"
NEMESIS_NAME = "PLEX COMPAT TEST (GUARDED)"
SERVICE_NAME = "plex-compat-test-guard"
PLEX_SHA256 = "bdd746d124a3efb3c86ca841c93ec5c2cae599b8c736ec66d96420b5971a3e7b"
PLEX_CERT_SHA256 = "b7c45789ad339affaecd51ef6be24c63786df75e9c273ac951b1cd1d755c2be0"
DEFAULT_APK = ROOT / "artifacts" / "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026-AUDIOSRC.apk"


def load_base():
    script = ROOT / "tools" / "build_standalone.py"
    spec = importlib.util.spec_from_file_location("safeplex_standalone_builder", script)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load standalone NEMESIS builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    overrides = {
        "STANDALONE": PROFILE,
        "NEMESIS_ID": NEMESIS_ID,
        "NEMESIS_NAME": NEMESIS_NAME,
        "SERVICE_NAME": SERVICE_NAME,
        "DIST_PREFIX": "plex-compat-test-guarded",
        "REPORT_SUFFIX": "compat-nemesis-test",
        "BUILD_LABEL": (
            "Plex compatibility APK with fullscreen and audio-source retention plus "
            "standalone Park Guard (NEMESIS package, no HMG-API dependency)"
        ),
        "PLEX_SHA256": PLEX_SHA256,
        "PLEX_CERT_SHA256": PLEX_CERT_SHA256,
    }
    for name, value in overrides.items():
        setattr(module, name, value)
    return module


def main():
    base = load_base()
    if "--apk" not in sys.argv:
        sys.argv.extend(["--apk", str(DEFAULT_APK)])
    base.main()


if __name__ == "__main__":
    main()
