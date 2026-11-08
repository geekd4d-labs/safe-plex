SAFE PLEX 0.2.0 (standalone) - PRIVATE TEST
=============================================

WHAT THIS IS

A NEMESIS package for the EV6 head unit. It installs the EV6 Plex build
plus a root guard service (safe-plex-guard). Unlike the HMG-API mod, this
package has no HMG dependency: the guard reads the head unit's own factory
vehicle services directly.

The guard force-stops Plex unless the car is confirmed safe:
  gear = Park, car not moving, speed under 0.5 km/h, no driving restriction.
Any missing or unreadable reading keeps Plex blocked (fail-closed). The
guard never modifies vehicle state; it only stops one app.

REQUIREMENTS

- The head unit must have NEMESIS installed and working (the same one the
  Jellyfin-on-GEN5W package uses).
- Android API 19, 32-bit ARM (the validated EV6 unit).
- Factory vehicle frameworks present:
  /system/framework/automotive.jar and /system/framework/com.hkmc.ext.hcan.jar
- No other SAFE PLEX (HMG mod or earlier standalone) installed at the same
  time.

INSTALL (USB)

1. Format the USB stick as FAT32.
2. Copy the contents of safe-plex-standalone-0.2.0-usb.zip onto the stick
   so the stick contains:
     Packages/plex.geekd4dlabs.safe.zip
     NEMESIS.data
     README-PRIVATE-TEST.txt
3. Insert the stick and use NEMESIS on the head unit to install
   plex.geekd4dlabs.safe.
4. If Plex was installed by hand before, uninstall it first
   (Settings > Apps) so the package's own copy is the one the guard covers.

VERIFY AFTER INSTALL

- NEMESIS shows the app and the safe-plex-guard service.
- logcat shows "started fail-closed supervisor (standalone; factory
  vehicle telemetry)" from StandaloneGuard.
- While the car is confirmed parked: Plex launches and plays video.
- While the car moves (or gear leaves Park, or a reading disappears):
  Plex is force-stopped within about a second and cannot be relaunched
  until the parked state holds for 1.5 s.
- /data/local/safe-plex/state shows version=1, ready=1 and a live pid.

UNINSTALL

Uninstall SAFE PLEX through NEMESIS. This stops the guard service,
force-stops Plex, and removes /data/local/safe-plex. Reinstall Plex from
the same package or from a plain APK as normal.

EXPECTED LIMITATIONS

- The binder calls (getGearPStatus / getCarSpeed / IsCarMoving /
  getStatus) are the same calls the EV6 Plex video gate makes, but they
  have NOT yet been run through this guard on your unit. Treat the first
  drive as a validation run and log any logcat line tagged StandaloneGuard.
- If a reading is unavailable at boot, Plex stays blocked until the
  factory services answer. That is the intended fail-closed behaviour.
