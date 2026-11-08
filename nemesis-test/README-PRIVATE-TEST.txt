PLEX COMPAT TEST 0.1.0 (GUARDED NEMESIS TEST)
================================================

PURPOSE

This separate NEMESIS test package contains the established private Plex changes
for the old Android 4.4 client on the Gen5W head unit:

- android.permission.GET_TASKS, required by this OEM firmware
- a current embedded Mozilla CA bundle, required for Plex HTTPS authentication
- fullscreen player window flags while preserving source aspect ratio
- the stable owner-controlled Android signing identity

It includes the fullscreen patch previously validated on the target EV6.

SAFETY BOUNDARY

The Park Guard remains mandatory because this package installs on a vehicle.
The guard is independent of Plex and has no HMG-API dependency. It reads the
factory vehicle services directly and force-stops com.plexapp.android unless
fresh telemetry confirms Park, no movement, near-zero speed, and no driving
restriction. Missing or invalid telemetry remains blocked.

This is not the unguarded bench/emulator artifact.

MIGRATION

Do not install this alongside any other SAFE PLEX package or HMG-API SAFE PLEX
mod. They own the same Android package and concurrent guards create ambiguous
uninstall and process-control behavior.

Before installation:

1. Remove the HMG-API SAFE PLEX mod or prior NEMESIS SAFE PLEX package using its
   own manager.
2. Confirm its guard service is stopped.
3. Confirm com.plexapp.android is absent before installing this package.

INSTALL

Extract the USB ZIP to the USB root. It must contain:

  Packages/plex.geekd4dlabs.compat-test.zip
  USB-NEMESIS.data
  README-PRIVATE-TEST.txt

Use NEMESIS to install PLEX COMPAT TEST (GUARDED).

FIRST VEHICLE TEST

Remain parked. Confirm Plex launches, authenticates, plays, and uses the expected
fullscreen player. Then validate:

- Park -> Reverse stops Plex
- Park -> Drive stops Plex
- launch while already unsafe cannot survive
- telemetry loss remains blocked
- returning to Park permits launch only after the safe debounce

APK identity

Package: com.plexapp.android
Version: 6.17.1.5294
SHA-256: d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f

This private test package contains proprietary Plex software. Do not redistribute
it publicly or include credentials, MFA codes, tokens, or private signing keys in
logs or reports.
