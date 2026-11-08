#!/usr/bin/env python3
"""Package the reviewed legacy Plex build for bench/emulator testing only."""
from pathlib import Path
import argparse
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APK_SHA256 = "d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f"
APK_NAME = "Plex-6.17.1.5294-EV6-COMPAT-TEST.apk"
ARCHIVE_NAME = "Plex-6.17.1.5294-EV6-COMPAT-TEST-1.zip"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
README = ROOT / "compat-test" / "README-BENCH-TEST.txt"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def zip_bytes(archive, name, data):
    info = zipfile.ZipInfo(name, ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def build(apk, output_dir):
    apk = Path(apk)
    output_dir = Path(output_dir)
    payload = apk.read_bytes()
    actual = sha256_bytes(payload)
    if actual != APK_SHA256:
        raise ValueError(f"APK SHA-256 mismatch: expected {APK_SHA256}, got {actual}")
    instructions = README.read_bytes()
    checksums = f"{APK_SHA256}  {APK_NAME}\n".encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / ARCHIVE_NAME
    with zipfile.ZipFile(output, "w") as archive:
        zip_bytes(archive, APK_NAME, payload)
        zip_bytes(archive, "README-BENCH-TEST.txt", instructions)
        zip_bytes(archive, "SHA256SUMS.txt", checksums)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("compatibility-test archive CRC failure")
        if sha256_bytes(archive.read(APK_NAME)) != APK_SHA256:
            raise ValueError("packaged APK SHA-256 mismatch")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apk",
        type=Path,
        default=ROOT / "artifacts" / "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist" / "compat-test")
    args = parser.parse_args()
    output = build(args.apk, args.output_dir)
    print(f"{sha256_bytes(output.read_bytes())}  {output}")


if __name__ == "__main__":
    main()
