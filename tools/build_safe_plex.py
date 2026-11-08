#!/usr/bin/env python3
"""Build and recursively verify the standalone (HMG-API independent) SAFE PLEX package.

The package is a NEMESIS package for the EV6 head unit: the EV6 Plex APK plus a
root guard service (app_process + StandaloneGuard) that reads the head unit's
own factory vehicle services. Deterministic: fixed ZIP timestamps, sorted
entries, recursive byte verification of every nested artifact.
"""
from pathlib import Path
import argparse
import configparser
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "package"
NEMESIS_ID = "plex.geekd4dlabs.safe"
NEMESIS_NAME = "SAFE PLEX"
SERVICE_NAME = "safe-plex-guard"
DIST_PREFIX = "safe-plex"
REPORT_SUFFIX = "safe-plex"
BUILD_LABEL = "SAFE PLEX production NEMESIS package (no HMG-API dependency)"
PLEX_SHA256 = "bdd746d124a3efb3c86ca841c93ec5c2cae599b8c736ec66d96420b5971a3e7b"
PLEX_CERT_SHA256 = "b7c45789ad339affaecd51ef6be24c63786df75e9c273ac951b1cd1d755c2be0"
PACKAGE = "com.plexapp.android"
VERSION_NAME = "6.17.1.5294"
LAUNCHER = "com.plexapp.plex.activities.SplashActivity"
STANDALONE_CLASSES = ("StandaloneGuard", "FactoryVehicleTelemetry")
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
DEFAULT_APK = ROOT / "artifacts" / "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026-AUDIOSRC.apk"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args, env=None):
    cmd = [str(a) for a in args]
    if os.name == "nt" and not Path(cmd[0]).suffix:
        for suffix in (".bat", ".cmd"):
            if Path(cmd[0] + suffix).is_file():
                cmd = ["cmd", "/c", cmd[0] + suffix, *cmd[1:]]
                break
    try:
        result = subprocess.run(
            cmd, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
    except subprocess.CalledProcessError as error:
        print(error.stdout or "", end="")
        raise
    print(result.stdout, end="")
    return result.stdout


def zip_bytes(archive, name, data, mode=0o100644):
    """Write deterministic ZIP metadata so identical inputs produce identical bytes."""
    info = zipfile.ZipInfo(str(name), ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = mode << 16
    archive.writestr(info, data)


def java_env(jdk):
    env = os.environ.copy()
    env["JAVA_HOME"] = str(jdk)
    env["PATH"] = str(jdk / "bin") + os.pathsep + env.get("PATH", "")
    return env


def find_sdk():
    candidates = [
        Path("/opt/data/toolchains/android-sdk"),
        Path.home() / "AppData/Local/Android/Sdk",
    ]
    for candidate in candidates:
        if (candidate / "platforms").is_dir():
            return candidate
    raise SystemExit("Android SDK not found; pass --sdk")


def find_jdk():
    candidates = [
        Path("/opt/data/toolchains/jdk"),
        Path.home() / "tools/jdk17",
    ]
    for candidate in candidates:
        if (candidate / "bin/javac").is_file() or (candidate / "bin/javac.exe").is_file():
            return candidate
    raise SystemExit("JDK 17 not found; pass --jdk")


def verify_plex_apk(apk, build_tools, env):
    if not apk.is_file() or sha256(apk) != PLEX_SHA256:
        raise SystemExit("Plex APK missing or SHA-256 mismatch")
    badging = run(build_tools / "aapt", "dump", "badging", apk)
    if f"package: name='{PACKAGE}'" not in badging or f"versionName='{VERSION_NAME}'" not in badging:
        raise SystemExit("wrong Plex package/version")
    if "sdkVersion:'16'" not in badging or "native-code: 'armeabi-v7a'" not in badging:
        raise SystemExit("wrong Plex API/ABI variant")
    if f"launchable-activity: name='{LAUNCHER}'" not in badging:
        raise SystemExit("wrong Plex launcher")
    signature = run(build_tools / "apksigner", "verify", "--min-sdk-version", "16",
                    "--verbose", "--print-certs", apk, env=env)
    if PLEX_CERT_SHA256 not in signature:
        raise SystemExit("unexpected Plex signing certificate")


def build_guard_jar(sdk, build_tools, jdk, build):
    classes = build / "standalone-classes"
    dex = build / "standalone-dex"
    shutil.rmtree(classes, ignore_errors=True)
    shutil.rmtree(dex, ignore_errors=True)
    classes.mkdir(parents=True)
    dex.mkdir(parents=True)
    android_jar = sdk / "platforms" / "android-35" / "android.jar"
    if not android_jar.exists():
        candidates = sorted((sdk / "platforms").glob("android-*/android.jar"))
        if not candidates:
            raise SystemExit("No Android platform android.jar installed")
        android_jar = candidates[-1]
    sources = sorted((ROOT / "service" / "src").rglob("*.java"))
    if not {path.stem for path in sources} >= set(STANDALONE_CLASSES):
        raise SystemExit("standalone guard sources missing from service/src")
    run(jdk / "bin" / "javac", "--release", "8", "-Xlint:-options", "-nowarn",
        "-cp", android_jar, "-d", classes, *sources)
    class_jar = build / "standalone-classes.jar"
    run(jdk / "bin" / "jar", "cf", class_jar, "-C", classes, ".")
    run(build_tools / "d8", "--release", "--min-api", "19", "--lib", android_jar,
        "--output", dex, class_jar, env=java_env(jdk))
    guard_jar = build / "safeplex-guard.jar"
    with zipfile.ZipFile(guard_jar, "w", zipfile.ZIP_DEFLATED) as archive:
        zip_bytes(archive, "classes.dex", (dex / "classes.dex").read_bytes())
    with zipfile.ZipFile(guard_jar) as archive:
        if archive.testzip() is not None or archive.namelist() != ["classes.dex"]:
            raise ValueError("invalid guard dex jar")
        dex_bytes = archive.read("classes.dex")
    for name in STANDALONE_CLASSES:
        if f"Ldev/geekd4dlabs/safeplex/{name};" not in dex_bytes.decode("latin-1"):
            raise ValueError(f"standalone class missing from dex: {name}")
    return guard_jar


def parse_nemesis(data):
    parser = configparser.ConfigParser(strict=True)
    parser.read_string(data)
    return parser


def verify_package(package, stage, guard_jar, apk):
    with zipfile.ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise ValueError("package CRC failure")
        checked = Path(tempfile.mkdtemp(prefix="safeplex-check-"))
        try:
            archive.extractall(checked)
            nemesis = parse_nemesis((checked / "NEMESIS.data").read_text())
        finally:
            shutil.rmtree(checked, ignore_errors=True)
    expect = {
        "nemesis": {"id": NEMESIS_ID, "name": NEMESIS_NAME,
                    "types": "application,service",
                    "preinstall": "scripts/pre.sh",
                    "preuninstall": "guard/preuninstall.sh"},
        "app.0": {"kind": "apk", "path": "app/Plex.apk", "package": PACKAGE,
                  "component": f"{PACKAGE}/{LAUNCHER}"},
        "service.0": {"name": SERVICE_NAME, "kind": "sh",
                      "path": "guard/safeplex-guard.sh", "uid": "root",
                      "mode": "restart"},
    }
    # Live NEMESIS 1.16.7 rejects the whole package when short-desc exceeds
    # 64 characters ("invalid package metadata: short-desc is over 64").
    short_desc = nemesis.get("nemesis", "short-desc", fallback="")
    if len(short_desc) > 64:
        raise ValueError(f"NEMESIS.data short-desc is {len(short_desc)} chars; max 64")
    for section, keys in expect.items():
        if not nemesis.has_section(section):
            raise ValueError(f"NEMESIS.data missing section {section}")
        for key, value in keys.items():
            if nemesis.get(section, key) != value:
                raise ValueError(f"NEMESIS.data {section}.{key} = "
                                 f"{nemesis.get(section, key)!r}, want {value!r}")
    with zipfile.ZipFile(package) as archive:
        for name in archive.namelist():
            path = stage / name
            if not path.is_file():
                raise ValueError(f"unexpected package entry: {name}")
            if archive.read(name) != path.read_bytes():
                raise ValueError(f"packaged bytes changed: {name}")
    if (stage / "app" / "Plex.apk").read_bytes() != apk.read_bytes():
        raise ValueError("packaged Plex bytes changed")
    if (stage / "guard" / "safeplex-guard.jar").read_bytes() != guard_jar.read_bytes():
        raise ValueError("packaged guard bytes changed")


def build_usb(package, usb, version):
    with zipfile.ZipFile(usb, "w", zipfile.ZIP_DEFLATED) as archive:
        zip_bytes(archive, f"Packages/{NEMESIS_ID}.zip", package.read_bytes())
        zip_bytes(archive, "NEMESIS.data",
                  (PROFILE / "src" / "USB-NEMESIS.data").read_bytes())
        zip_bytes(archive, "README.txt",
                  (PROFILE / "README.txt").read_bytes())
    with zipfile.ZipFile(usb) as archive:
        if archive.testzip() is not None:
            raise ValueError("USB CRC failure")
        if archive.read(f"Packages/{NEMESIS_ID}.zip") != package.read_bytes():
            raise ValueError("nested package differs from built package")
        parser = parse_nemesis(archive.read("NEMESIS.data").decode())
        if parser.get("nemesis", "type") != "install" \
                or parser.get("nemesis", "path") != f"Packages/{NEMESIS_ID}.zip":
            raise ValueError("USB NEMESIS.data does not point at the package")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path,
                        default=ROOT / "artifacts" / "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk")
    parser.add_argument("--sdk", type=Path, default=None)
    parser.add_argument("--jdk", type=Path, default=None)
    parser.add_argument("--build-tools-version", default="36.0.0")
    args = parser.parse_args()

    version = (PROFILE / "VERSION").read_text().strip()
    sdk = (args.sdk or find_sdk()).resolve()
    jdk = (args.jdk or find_jdk()).resolve()
    build_tools = sdk / "build-tools" / args.build_tools_version
    env = java_env(jdk)
    apk = args.apk.resolve()
    verify_plex_apk(apk, build_tools, env)

    nemesis_source = (PROFILE / "src" / "NEMESIS.data").read_text()
    parser = parse_nemesis(nemesis_source)
    if parser.get("nemesis", "package-version") != version:
        raise SystemExit("NEMESIS.data package-version does not match standalone/VERSION")

    build = ROOT / "build"
    dist = ROOT / "dist"
    build.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)
    guard_jar = build_guard_jar(sdk, build_tools, jdk, build)

    package_zip = dist / f"{NEMESIS_ID}.zip"
    usb_zip = dist / f"{DIST_PREFIX}-{version}-usb.zip"

    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary) / "package"
        (stage / "app").mkdir(parents=True)
        (stage / "guard").mkdir()
        (stage / "scripts").mkdir()
        # copyfile: byte-exact. write_text would re-encode line endings
        # (CRLF on Windows), corrupting the NEMESIS descriptor on-device.
        shutil.copyfile(PROFILE / "src" / "NEMESIS.data", stage / "NEMESIS.data")
        shutil.copyfile(apk, stage / "app" / "Plex.apk")
        shutil.copyfile(guard_jar, stage / "guard" / "safeplex-guard.jar")
        shutil.copyfile(PROFILE / "src" / "guard" / "safeplex-guard.sh",
                        stage / "guard" / "safeplex-guard.sh")
        shutil.copyfile(PROFILE / "src" / "guard" / "preuninstall.sh",
                        stage / "guard" / "preuninstall.sh")
        shutil.copyfile(PROFILE / "src" / "scripts" / "pre.sh",
                        stage / "scripts" / "pre.sh")
        with zipfile.ZipFile(package_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    mode = 0o100755 if path.suffix == ".sh" else 0o100644
                    zip_bytes(archive, path.relative_to(stage), path.read_bytes(), mode)
        verify_package(package_zip, stage, guard_jar, apk)
        build_usb(package_zip, usb_zip, version)

    artifacts = {path.name: sha256(path) for path in (apk, guard_jar, package_zip, usb_zip)}
    report = {
        "scope": "host-built and structurally verified; NOT vehicle validated",
        "build": BUILD_LABEL,
        "plex": {"sha256": PLEX_SHA256, "certificate_sha256": PLEX_CERT_SHA256},
        "guard_entry": "dev.geekd4dlabs.safeplex.StandaloneGuard",
        "artifacts": artifacts,
    }
    (dist / f"VERIFICATION-{REPORT_SUFFIX}.json").write_text(json.dumps(report, indent=2) + "\n")
    (dist / f"SHA256SUMS-{REPORT_SUFFIX}.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in artifacts.items()))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if "--apk" not in sys.argv:
        sys.argv.extend(["--apk", str(DEFAULT_APK)])
    main()
