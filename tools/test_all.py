#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JDK = Path(os.environ.get("JAVA_HOME", "/opt/data/toolchains/jdk"))
BUILD = ROOT / "build" / "test-classes"


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def main():
    run("python3", "-m", "unittest", "discover", "-s", "tests", "-v")
    run("python3", "tools/test_integration.py")
    run("python3", "tools/test_packaging.py")
    run("python3", "tools/test_standalone.py")
    run("python3", "tools/test_compat_test.py")
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    package = ROOT / "service/src/dev/geekd4dlabs/safeplex"
    production = [
        package / "SafetyPolicy.java",
        package / "ParkState.java",
        package / "EnforcementLatch.java",
        package / "ProcessDeadline.java",
        package / "ProcessName.java",
        package / "VehicleResponse.java",
        package / "FactoryVehicleTelemetry.java",
    ]
    tests = sorted((ROOT / "service/test").rglob("*.java"))
    run(JDK / "bin/javac", "--release", "8", "-Xlint:-options", "-nowarn", "-d", BUILD, *production, *tests)
    for test in ["SafetyPolicyTest", "ParkStateTest", "EnforcementLatchTest", "ProcessDeadlineTest", "ProcessNameTest", "VehicleResponseTest", "FactoryVehicleTelemetryTest"]:
        run(JDK / "bin/java", "-cp", BUILD, "dev.geekd4dlabs.safeplex." + test)


if __name__ == "__main__":
    main()
