#!/usr/bin/env python3
"""Host-side contract tests for the production SAFE PLEX NEMESIS package.

No Android SDK required: parses the package descriptors, checks the shell
scripts and Java sources against the validated EV6 pattern, and verifies the
deterministic ZIP helpers behave identically to the HMG build.
"""
import importlib.util
import configparser
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "package" / "src"
PROFILE_SRC = ROOT / "package"
SERVICE = ROOT / "service" / "src" / "dev" / "geekd4dlabs" / "safeplex"
ID = "plex.geekd4dlabs.safe"


def read(path):
    return path.read_bytes()


def check_nemesis_data():
    raw = read(SRC / "NEMESIS.data")
    assert b"\r\n" not in raw, "NEMESIS.data has CRLF line endings"
    parser = configparser.ConfigParser(strict=True)
    parser.read_string(raw.decode())
    assert parser.get("nemesis", "id") == ID
    assert parser.get("nemesis", "name") == "SAFE PLEX"
    assert parser.get("nemesis", "types") == "application,service"
    assert parser.get("nemesis", "type") == "application,service"
    assert parser.get("nemesis", "models") == "cvev_us,neev_us,neev23_us"
    assert parser.get("nemesis", "os") == "CVEV.USA.0000.V015.012.260507"
    assert parser.get("nemesis", "depends") == "!plex.geekd4dlabs.compat-test"
    assert len(parser.get("nemesis", "short-desc")) <= 64, "NEMESIS rejects short-desc over 64 chars"
    assert len(parser.get("nemesis", "detailed-desc")) <= 256, \
        "NEMESIS 1.1 rejects detailed-desc over 256 chars"
    descriptor = raw.decode()
    assert "Kia/Hyundai Gen5W" in descriptor
    assert "0.1.3 runtime" in parser.get("nemesis", "detailed-desc")
    version = (PROFILE_SRC / "VERSION").read_text().strip()
    assert f"the {version} archive is not vehicle-installed" in \
        parser.get("nemesis", "detailed-desc")
    assert "EV6" not in parser.get("nemesis", "short-desc"), \
        "package summary must not select an EV6-only profile"
    assert parser.get("nemesis", "preinstall") == "scripts/pre.sh"
    assert parser.get("nemesis", "preuninstall") == "guard/preuninstall.sh"
    assert parser.get("nemesis", "package-version") == (PROFILE_SRC / "VERSION").read_text().strip()
    assert parser.get("app.0", "kind") == "apk"
    assert parser.get("app.0", "path") == "app/Plex.apk"
    assert parser.get("app.0", "package") == "com.plexapp.android"
    assert parser.get("app.0", "component") == "com.plexapp.android/com.plexapp.plex.activities.SplashActivity"
    assert parser.get("service.0", "name") == "safe-plex-guard"
    assert parser.get("service.0", "kind") == "sh"
    assert parser.get("service.0", "path") == "guard/safeplex-guard.sh"
    assert parser.get("service.0", "uid") == "root"
    assert parser.get("service.0", "mode") == "restart"


def check_usb_nemesis_data():
    raw = read(SRC / "USB-NEMESIS.data")
    assert b"\r\n" not in raw, "USB-NEMESIS.data has CRLF line endings"
    parser = configparser.ConfigParser(strict=True)
    parser.read_string(raw.decode())
    assert parser.get("nemesis", "type") == "install"
    assert parser.get("nemesis", "path") == f"Packages/{ID}.zip"


def check_scripts():
    guard = read(SRC / "guard" / "safeplex-guard.sh").decode()
    pre = read(SRC / "scripts" / "pre.sh").decode()
    preuninstall = read(SRC / "guard" / "preuninstall.sh").decode()
    # Head-unit sh requires LF line endings.
    for name, text in (("guard", guard), ("pre", pre), ("preuninstall", preuninstall)):
        assert "\r\n" not in text, f"{name}.sh has CRLF line endings"
    # Fail-closed preflight: wrong API or missing vehicle frameworks must abort.
    assert 'ro.build.version.sdk' in guard
    assert "/system/framework/automotive.jar" in guard
    assert "/system/framework/com.hkmc.ext.hcan.jar" in guard
    # It launches the standalone entry point, not the HMG one.
    assert "dev.geekd4dlabs.safeplex.StandaloneGuard" in guard
    assert "dev.geekd4dlabs.safeplex.SafePlexGuard" not in guard
    assert "/system/bin/app_process" in guard
    assert "guard/safeplex-guard.jar" in guard
    # Double-start protection: boot-id + pid lock, stale lock from a prior
    # boot is reclaimed.
    assert "boot_id" in guard
    assert 'mkdir "$DIR/lock"' in guard
    # Cleanup path force-stops Plex before the guard jar can be removed.
    assert "cleanup" in guard
    assert 'PKG=com.plexapp.android' in guard
    assert 'am force-stop "$PKG"' in guard
    # pre.sh gate.
    assert 'ro.build.version.sdk' in pre
    assert "19" in pre
    assert "automotive.jar" in pre
    assert "com.hkmc.ext.hcan.jar" in pre
    # preuninstall: stop the app, then reuse the guard's cleanup.
    assert "am force-stop com.plexapp.android" in preuninstall
    assert "safeplex-guard.sh" in preuninstall and "cleanup" in preuninstall


def check_guard_java():
    text = (SERVICE / "StandaloneGuard.java").read_text()
    # Same policy constants, same enforcement path as the HMG guard.
    assert "SafePlexGuard.SAFE_DEBOUNCE_MS" in text
    assert "SafePlexGuard.MAX_SAMPLE_AGE_MS" in text
    assert "SafePlexGuard.REPEAT_FORCE_STOP_MS" in text
    assert "SafePlexGuard.POLL_MS" in text
    assert "SafePlexGuard.enforcePlexStopped()" in text
    assert "SafetyPolicy.isSafe" in text
    # Telemetry comes from the factory services, never the HMG socket.
    assert "FactoryVehicleTelemetry.read()" in text
    assert "VehicleTelemetry.read()" not in text.replace("FactoryVehicleTelemetry.read()", "")
    # It is the standalone entry point, launched by the NEMESIS service.
    assert "public static void main(String[] args)" in text
    # Fail-closed: any error keeps the state blocked.
    assert "state.accept(false, SystemClock.elapsedRealtime())" in text
    # One shared policy state + latch, same as the HMG guard.
    assert "new ParkState(" in text and "new EnforcementLatch(" in text
    assert "safe-plex-standalone-enforcer" in text


def check_telemetry_java():
    text = (SERVICE / "FactoryVehicleTelemetry.java").read_text()
    # Reflection-only Android access: no android.* imports (host-compilable).
    for line in text.splitlines():
        if line.startswith("import"):
            assert line.startswith("import java."), "must not import android.* directly: " + line
    # Same four values as the HMG-API Hub.
    for service in ("getGearPStatus", "getCarSpeed", "IsCarMoving", "getStatus"):
        assert service in text
    # The validated EV6 gate's jar paths and service contract.
    assert "/system/framework/automotive.jar" in text
    assert "/system/framework/com.hkmc.ext.hcan.jar" in text
    assert "asInterface" in text
    assert "isBinderAlive" in text
    # Fail-closed: unanswered reading is "-", never fabricated.
    assert 'NO_RESPONSE = "-"' in text
    # Stale binders are dropped when a reading fails.
    assert "invalidateServices()" in text


def check_zip_helpers():
    spec = importlib.util.spec_from_file_location("build_safe_plex", ROOT / "tools" / "build_safe_plex.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as temp:
        temp_dir = Path(temp)
        for name in ("a.zip", "b.zip"):
            with zipfile.ZipFile(temp_dir / name, "w") as archive:
                module.zip_bytes(archive, "x.bin", b"same-bytes", mode=0o100644)
                module.zip_bytes(archive, "y.sh", b"same-bytes", mode=0o100755)
        assert (temp_dir / "a.zip").read_bytes() == (temp_dir / "b.zip").read_bytes(), \
            "zip_bytes must be deterministic"
        package = temp_dir / f"{ID}.zip"
        usb_a = temp_dir / "usb-a.zip"
        usb_b = temp_dir / "usb-b.zip"
        package.write_bytes(b"fake-package-bytes")
        version = (PROFILE_SRC / "VERSION").read_text().strip()
        module.build_usb(package, usb_a, version)
        module.build_usb(package, usb_b, version)
        assert usb_a.read_bytes() == usb_b.read_bytes(), "USB packaging must be deterministic"
        with zipfile.ZipFile(usb_a) as archive:
            assert archive.namelist() == [f"Packages/{ID}.zip",
                                          "NEMESIS.data", "README.txt"]
            assert archive.read(f"Packages/{ID}.zip") == b"fake-package-bytes"
            usb_descriptor = archive.read("NEMESIS.data").decode()
            assert "type=install" in usb_descriptor
            assert f"path=Packages/{ID}.zip" in usb_descriptor


def main():
    check_nemesis_data()
    check_usb_nemesis_data()
    check_scripts()
    check_guard_java()
    check_telemetry_java()
    check_zip_helpers()
    print("standalone contract tests: 6 passed")


if __name__ == "__main__":
    main()
