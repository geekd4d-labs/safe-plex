PLEX COMPAT TEST 0.1.3 (GUARDED NEMESIS TEST)
================================================

PURPOSE

This separate NEMESIS test package contains the established private Plex changes
for the old Android 4.4 client on the Gen5W head unit:

- android.permission.GET_TASKS, required by this OEM firmware
- a current embedded Mozilla CA bundle, required for Plex HTTPS authentication
- fullscreen player window flags while preserving source aspect ratio
- audio source retention, so stopping playback does not hand the head unit
  back to FM radio
- the stable owner-controlled Android signing identity

It includes the fullscreen patch previously validated on the target EV6, plus
the audio source fix validated on the target EV6 in 0.1.3.

AUDIO SOURCE BEHAVIOR

Stock Plex abandons Android audio focus when a player stops, and the Gen5W
AudioServiceHelper then auto-restores the previous AV source, which surfaces as
FM radio appearing over Plex. A stopping player now hands focus to a
process-wide no-op holder before releasing its own listener, so Plex remains
the foreground AV source and the head unit stays put.

This does not defeat the guard. A guard force-stop kills the Plex process, so
Android releases the holder and the head unit resumes its normal source.

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
  NEMESIS.data
  README-PRIVATE-TEST.txt

Use NEMESIS to install PLEX COMPAT TEST (GUARDED).

FIRST VEHICLE TEST

Remain parked. Confirm Plex launches, authenticates, plays, and uses the expected
fullscreen player. Then validate:

- pausing and stopping playback does not pop up FM radio
- Park -> Reverse stops Plex
- Park -> Drive stops Plex
- launch while already unsafe cannot survive
- telemetry loss remains blocked
- returning to Park permits launch only after the safe debounce
- after a guard stop while driving, the head unit returns to its normal source

APK identity

Package: com.plexapp.android
Version: 6.17.1.5294
SHA-256: bdd746d124a3efb3c86ca841c93ec5c2cae599b8c736ec66d96420b5971a3e7b

This private test package contains proprietary Plex software. Do not redistribute
it publicly or include credentials, MFA codes, tokens, or private signing keys in
logs or reports.
