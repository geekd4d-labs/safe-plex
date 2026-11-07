#!/usr/bin/env python3
"""Build and recursively verify the private HMG-API SAFE PLEX mod."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HMG_COMMIT = "180185de2c57afb2cca4858d0be7828e8f1051d6"
HMG_AUTHOR_UUID = "96f22dc5-6d6e-8098-bbc9-e554834eb78d"
PLEX_SHA256 = "d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f"
PLEX_CERT_SHA256 = "b7c45789ad339affaecd51ef6be24c63786df75e9c273ac951b1cd1d755c2be0"
PACKAGE = "com.plexapp.android"
VERSION_NAME = "6.17.1.5294"
LAUNCHER = "com.plexapp.plex.activities.SplashActivity"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


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


def zip_bytes(archive, name, data):
    """Write deterministic ZIP metadata so identical inputs produce identical bytes."""
    info = zipfile.ZipInfo(str(name), ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def write_usb(mod, usb, instructions):
    with zipfile.ZipFile(usb, "w", zipfile.ZIP_DEFLATED) as archive:
        zip_bytes(archive, "HMGAPI/updates/" + mod.name, mod.read_bytes())
        zip_bytes(archive, "README-PRIVATE-TEST.txt", instructions.encode())


def verify_usb(mod, usb):
    with zipfile.ZipFile(usb) as archive:
        if archive.testzip() is not None:
            raise ValueError("USB CRC failure")
        path = "HMGAPI/updates/" + mod.name
        if path not in archive.namelist():
            raise ValueError("USB update path missing")
        nested = archive.read(path)
        if nested != mod.read_bytes():
            raise ValueError("nested mod differs from signed archive")
        try:
            with zipfile.ZipFile(io.BytesIO(nested)) as inner:
                if inner.testzip() is not None:
                    raise ValueError("nested mod CRC failure")
                if "mod.json" not in inner.namelist():
                    raise ValueError("nested mod descriptor missing")
        except zipfile.BadZipFile as error:
            raise ValueError("nested mod is not a ZIP") from error


def java_env(jdk):
    env = os.environ.copy()
    env["JAVA_HOME"] = str(jdk)
    env["PATH"] = str(jdk / "bin") + os.pathsep + env.get("PATH", "")
    return env


def build_service(sdk, build_tools, jdk, build):
    classes = build / "service-classes"
    dex = build / "service-dex"
    classes.mkdir(parents=True, exist_ok=True)
    dex.mkdir(parents=True, exist_ok=True)
    android_jar = sdk / "platforms" / "android-35" / "android.jar"
    if not android_jar.exists():
        candidates = sorted((sdk / "platforms").glob("android-*/android.jar"))
        if not candidates:
            raise SystemExit("No Android platform android.jar installed")
        android_jar = candidates[-1]
    sources = sorted((ROOT / "service" / "src").rglob("*.java"))
    run(jdk / "bin" / "javac", "--release", "8", "-Xlint:-options", "-nowarn",
        "-cp", android_jar, "-d", classes, *sources)
    class_jar = build / "service-classes.jar"
    run(jdk / "bin" / "jar", "cf", class_jar, "-C", classes, ".")
    run(build_tools / "d8", "--release", "--min-api", "19", "--lib", android_jar,
        "--output", dex, class_jar, env=java_env(jdk))
    service_jar = build / "safe-plex-guard.jar"
    with zipfile.ZipFile(service_jar, "w", zipfile.ZIP_DEFLATED) as archive:
        zip_bytes(archive, "classes.dex", (dex / "classes.dex").read_bytes())
    with zipfile.ZipFile(service_jar) as archive:
        if archive.testzip() is not None or archive.namelist() != ["classes.dex"]:
            raise ValueError("invalid service dex jar")
    return service_jar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hmg-source", type=Path, required=True)
    parser.add_argument("--author-key", type=Path, required=True)
    parser.add_argument("--apk", type=Path, default=ROOT / "artifacts" / "Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk")
    parser.add_argument("--sdk", type=Path, default=Path("/opt/data/toolchains/android-sdk"))
    parser.add_argument("--jdk", type=Path, default=Path("/opt/data/toolchains/jdk"))
    parser.add_argument("--build-tools-version", default="36.0.0")
    args = parser.parse_args()

    source = args.hmg_source.resolve()
    if run("git", "-C", source, "rev-parse", "HEAD").strip() != HMG_COMMIT:
        raise SystemExit("Refusing unreviewed HMG-API source")
    if run("git", "-C", source, "status", "--porcelain").strip():
        raise SystemExit("Refusing modified HMG-API source")

    sdk = args.sdk.resolve()
    jdk = args.jdk.resolve()
    build_tools = sdk / "build-tools" / args.build_tools_version
    env = java_env(jdk)
    apk = args.apk.resolve()
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

    build = ROOT / "build"
    dist = ROOT / "dist"
    shutil.rmtree(build / "service-classes", ignore_errors=True)
    shutil.rmtree(build / "service-dex", ignore_errors=True)
    build.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)
    service_jar = build_service(sdk, build_tools, jdk, build)

    engine = build / "hmg-engine"
    shutil.rmtree(engine, ignore_errors=True)
    engine.mkdir(parents=True)
    run(jdk / "bin" / "javac", "--release", "8", "-Xlint:-options", "-nowarn",
        "-d", engine, *sorted((source / "core" / "runtime" / "java" / "hmgapi" / "engine").glob("*.java")))

    key = args.author_key.resolve()
    if key.is_relative_to(ROOT):
        raise SystemExit("author key must remain outside repository")
    if not key.is_file() or not Path(str(key) + ".pub").is_file():
        raise SystemExit("established author key and paired .pub file are required")

    descriptor = json.loads((ROOT / "mod" / "mod.json").read_text())
    descriptor["version"] = (ROOT / "VERSION").read_text().strip()
    name = descriptor["id"] + "-" + descriptor["version"]
    mod_zip = dist / (name + ".zip")
    instructions = (ROOT / "README.md").read_text()

    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary) / "mod"
        (stage / "app").mkdir(parents=True)
        (stage / "svc").mkdir()
        (stage / "mod.json").write_text(json.dumps(descriptor, indent=2) + "\n")
        shutil.copyfile(apk, stage / "app" / "Plex.apk")
        shutil.copyfile(service_jar, stage / "svc" / "safe-plex-guard.jar")
        (stage / "PRIVATE-TEST.txt").write_text(instructions)
        signing = run(jdk / "bin" / "java", "-cp", engine, "hmgapi.engine.Signing", "sign", stage, key)
        if ("uuid " + HMG_AUTHOR_UUID) not in signing:
            raise SystemExit("refusing unexpected HMG author identity")
        with zipfile.ZipFile(mod_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    zip_bytes(archive, path.relative_to(stage), path.read_bytes())
        checked = Path(temporary) / "checked"
        checked.mkdir()
        with zipfile.ZipFile(mod_zip) as archive:
            if archive.testzip() is not None:
                raise ValueError("mod CRC failure")
            archive.extractall(checked)
        verified = run(jdk / "bin" / "java", "-cp", engine, "hmgapi.engine.Signing", "verify", checked)
        if ("uuid " + HMG_AUTHOR_UUID) not in verified:
            raise SystemExit("packaged HMG author identity mismatch")
        if (checked / "app" / "Plex.apk").read_bytes() != apk.read_bytes():
            raise ValueError("packaged Plex bytes changed")
        if (checked / "svc" / "safe-plex-guard.jar").read_bytes() != service_jar.read_bytes():
            raise ValueError("packaged SAFE PLEX guard bytes changed")
        if json.loads((checked / "mod.json").read_text()) != descriptor:
            raise ValueError("packaged descriptor changed")

    usb = dist / (name + "-usb.zip")
    write_usb(mod_zip, usb, instructions)
    verify_usb(mod_zip, usb)
    artifacts = {path.name: sha256(path) for path in (apk, service_jar, mod_zip, usb)}
    report = {
        "scope": "host-built and structurally verified; NOT vehicle validated",
        "hmg_commit": HMG_COMMIT,
        "hmg_author_uuid": HMG_AUTHOR_UUID,
        "plex": {"sha256": PLEX_SHA256, "certificate_sha256": PLEX_CERT_SHA256},
        "artifacts": artifacts,
    }
    (dist / "VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    (dist / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in artifacts.items()))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
