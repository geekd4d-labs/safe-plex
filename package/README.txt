SAFE PLEX 1.1.0
=================

PARKED USE ONLY. SAFE PLEX is meant for a fully stopped vehicle in Park.
Watching video while driving may be restricted or illegal where you live.
Do not remove or weaken the Park Guard.


WHAT THIS IS

A NEMESIS package for the Kia/Hyundai Gen5W head unit. It installs a Plex
build patched for this old Android 4.4 system, plus a root guard service
(safe-plex-guard) that blocks Plex whenever the car is not safely parked.

The guard reads the head unit's own factory vehicle services directly. It
has no HMG-API dependency.

Plex is permitted only while all four readings agree the car is safe:
gear in Park, not moving, speed under 0.5 km/h, and no driving restriction.
Anything else -- including a missing, stale, or unreadable value -- blocks
Plex. This is deliberate: if the guard cannot prove the car is parked, it
assumes it is not. The guard never changes vehicle state; it only stops
one app.


REQUIREMENTS

- NEMESIS installed and working on the head unit.
- Gen5W Android 4.4.2 / API 19, 32-bit ARM.
- Factory vehicle frameworks present:
    /system/framework/automotive.jar
    /system/framework/com.hkmc.ext.hcan.jar
- No other SAFE PLEX or Plex install present at the same time.


INSTALL (USB)

1. Format a USB stick as FAT32.
2. Extract safe-plex-1.1.0-usb.zip to the root of the stick, so it contains:
     Packages/plex.geekd4dlabs.safe.zip
     NEMESIS.data
     README.txt
3. Insert the stick and install SAFE PLEX through NEMESIS.

UPGRADING FROM THE EARLIER TEST PACKAGE

If "PLEX COMPAT TEST (GUARDED)" (plex.geekd4dlabs.compat-test) is installed,
uninstall it through NEMESIS first. Both own com.plexapp.android, and running
two guards at once makes uninstall and process control ambiguous.

Uninstalling clears Plex app data, so you will sign in again afterward.


USING PLEX ON THIS HEAD UNIT

Sign in with a Plex account. The "Sign in with Google" button does not work
on this build yet; it needs a browser component this system does not have.
Use the email-and-password form instead.

If your Plex account uses two-factor authentication, this old client has no
separate field for the code. Type your password and the six-digit code
together as one string, with no space. If your password is
NobodyWillGuessThisPassword and your current code is 123456, enter:

    NobodyWillGuessThisPassword123456

The code expires quickly, so have it ready before you tap the field.

For the smoothest playback, set your Plex transcode quality to 720p. This
head unit is a 2014-era Android device and higher settings stutter or fail
to start.


WHAT TO EXPECT

- NEMESIS lists the app and the safe-plex-guard service.
- Plex launches and plays video while parked.
- Video fills the screen without stretching or cropping.
- Stopping or pausing playback does not switch the head unit back to FM radio.
- Leaving Park, or moving, force-stops Plex within about a second.
- Returning to Park allows Plex again after the parked state holds 1.5 s.
- /data/local/safe-plex/state shows version=1, ready=1 and a live pid.


UNINSTALL

Uninstall SAFE PLEX through NEMESIS. That stops the guard, force-stops Plex,
and removes /data/local/safe-plex.


NOTES AND LIMITS

- Validated on a 2022 US Kia EV6 (Gen5W). Other models and firmware are
  untested; treat a first install elsewhere as a validation run.
- If the factory services do not answer at boot, Plex stays blocked until
  they do. That is the intended fail-closed behavior.
- This package contains proprietary Plex software. Do not redistribute it,
  and keep credentials, codes, tokens, and signing keys out of any logs or
  reports you share.
