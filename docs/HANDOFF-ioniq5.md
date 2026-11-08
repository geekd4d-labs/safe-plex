# Handoff: porting SAFE PLEX to Ioniq 5 head units

Written for a fresh session with no prior context. Read this before touching
anything. The validated target so far is a **2022 US Kia EV6, Gen5W**.

## What SAFE PLEX is

Two things shipped as one NEMESIS package:

1. **Plex Android `6.17.1.5294`, patched** to run on a Gen5W head unit
   (Android 4.4.2 / API 19, 32-bit ARM).
2. **A root Park Guard service** (`safe-plex-guard`) that force-stops Plex
   unless the car's own factory vehicle services prove it is safely parked.

Current release: `1.1.0`, package id `plex.geekd4dlabs.safe`, display name
`SAFE PLEX`. Repo: `/opt/data/projects/Ev6/safe-plex` → GitHub
`geekd4d-labs/safe-plex` (private).

Read `README.md` for how it works and `docs/device-validation.md` for exactly
what has and has not been proven on a vehicle.

## Non-negotiable safety rules

The owner's original requirement: *"I want to make it so we cant use it if the
car is moving just like VLC."* Everything below follows from that.

- The guard is **fail-closed**. It does not detect motion; it demands positive
  proof of Park. Missing, malformed, contradictory, stale, or unanswered
  telemetry blocks Plex. Never invert this into "block only when motion is
  detected" — an unreadable sensor would then mean "allowed".
- The guard **starts blocked**.
- Process matching is **exact**: `com.plexapp.android` and its
  `com.plexapp.android:` children only. Never prefix-match; it would kill
  bystander apps.
- Never ship an in-vehicle artifact without the guard. A bench/emulator-only
  archive exists (`tools/build_compat_test.py`) and must never be installed in
  a car.
- Do not loosen the compatibility gate to make another vehicle "just work."
  Add a separate profile and physically validate it.

## Build environment

Host tooling runs in this container; APK signing and ADB run on a Mac.

| What | Where |
| --- | --- |
| Repo | `/opt/data/projects/Ev6/safe-plex` |
| APK work trees | `/opt/data/projects/Ev6/Plex/build/` |
| Apktool 3.0.3 | `/opt/data/projects/Ev6/Plex/apktool_3.0.3.jar` |
| JDK | `/opt/data/toolchains/jdk` |
| Mac build host | `ssh -i /opt/data/.ssh/chell_ed25519 geekd4d@Applied-Science.geekd4d.com` |
| Android build-tools | `$ANDROID_HOME/build-tools/36.0.0` on the Mac |
| Signing keystore | `~/hmg-private/keys/plex-car-test.p12` on the Mac, alias `plex-car-test` |
| Keystore passwords | `~/hmg-private/keys/plex-car-test.pass`, `...-key.pass` (file refs only — never print or paste) |
| ADB | `/opt/homebrew/bin/adb` on the Mac |
| EV6 head unit serial | `000021111709414700C5` |

Commands:

```bash
python3 tools/test_all.py          # full suite: patcher, package contracts, Java guard
python3 tools/build_safe_plex.py   # builds dist/safe-plex-<version>-usb.zip
```

Sign on the Mac with `zipalign -f -p 4` then `apksigner sign --min-sdk-version 16
--v1-signing-enabled true --v2-signing-enabled false`. **Android 4.4 needs the v1
(JAR) signature**; a v2-only APK will not install.

Always reuse the same signing key: same-key updates install in place and preserve
the user's Plex login. A new key forces an uninstall, which wipes app data.

## The Plex compatibility patches

All implemented in `scripts/patch_decoded.py`, which is idempotent and applies to
an apktool-decoded tree. Unit tests: `tests/test_patch_decoded.py`. Each patch
exists because the firmware required it — keep the set minimal.

1. **`android.permission.GET_TASKS`** — this OEM firmware needs it even when Plex
   calls `Activity.finish()`.
2. **Current Mozilla CA bundle** (`vendor/cacert-2026-11-05.pem`) replacing Plex's
   2011 bundle. Without it, login fails with `libcurl` certificate error 60.
   Certificate verification stays enabled — do not disable it.
3. **`FLAG_FULLSCREEN`** on both mobile video-player activities, removing the Gen5W
   90-pixel status-bar inset. Inset only — never zoom, stretch, or crop.
4. **Audio source retention** — see below.
5. **Stable owner-controlled v1 signing identity.**

### Audio source retention (the subtle one)

Stock Plex calls `abandonAudioFocus` when a player stops. Gen5W's
`AudioServiceHelper` reads that as "nothing is playing" and auto-restores the
previous AV source, so **FM radio pops up over Plex** on stop.

Fix, in `com/plexapp/plex/audioplayer/a.smali`: a stopping player hands focus to a
process-wide no-op holder (`EV6FocusHolder`) *before* abandoning its own listener,
sets an `ev6Released` flag so it ignores the resulting focus-loss callback, and
clears that flag on the next focus request.

This is safe only because the holder is **process-scoped** — a guard force-stop
kills the process and Android releases the holder automatically. If you ever move
focus-holding into a surviving process or service, you break that property and the
head unit could be stuck on a dead source while driving.

Verify in logcat: `ModeManagerService: isAvModePackage : com.plexapp.android`
after Stop. Filter out `RadioService|RDO_MICOM|HDBandScan` scan noise.

## NEMESIS packaging gotchas

The live parser (NEMESIS 1.16.7) is stricter than its docs. Each of these cost a
release:

- Package descriptor uses **`types=`** (plural). The USB root descriptor uses
  singular **`type=install`**.
- **`short-desc` must be ≤ 64 characters** or the whole install fails with
  `invalid package metadata`.
- The USB root descriptor must be named exactly **`NEMESIS.data`**.
- `package-version` must be dotted numbers.

Before publishing, validate against the head unit's own parser rather than a
host-side INI check:

```bash
adb push <inner-package>.zip /data/local/tmp/
adb shell "nemesis pkg-info /data/local/tmp/<inner-package>.zip"
```

Require parsed metadata plus `compat=full`.

Debugging an install failure: the reason lands in
`/data/nemesis/logs/usb-handler/usb-handler.log`, **not** `/data/nemesis/nemesis.log`.
The Manager's exported log is often empty.

Root commands run via `nemesis root -c "<cmd>"`. For `pm install -r`, wrap it as
`setprop sys.boot_completed 0; pm install -r <apk>; setprop sys.boot_completed 1`.

Other field notes: inserting a USB stick can drop the ADB cable session; an
HMG-API mod uninstall can leave the Android APK installed, so always confirm with
`pm path com.plexapp.android`.

## Park Guard internals

Java source in `service/src/dev/geekd4dlabs/safeplex/`, host tests in
`service/test/`. Runs under `app_process`, NEMESIS service `kind=sh`, `uid=root`,
`mode=restart`. Shell wrapper `package/src/guard/safeplex-guard.sh` does an
API-19 and vehicle-framework preflight and holds a boot-id/pid double-start lock.

Policy: Plex permitted only while `gear.park == 1`, `moving == 0`,
`abs(speed) <= 0.5 km/h`, and `driving.restricted == 0` all hold for 1.5 s.
Enforcement repeats `am force-stop` once per second while blocked, with an exact
`/proc` match fallback. State file: `/data/local/safe-plex/state`.

Telemetry comes from factory binders:

- `ISystemService.getGearPStatus()` — `/system/framework/automotive.jar`
- `ITM_HSCANService.getCarSpeed(0)` / `IsCarMoving()` — `/system/framework/com.hkmc.ext.hcan.jar`
- `IRegulationManager.getStatus()` — `/system/framework/automotive.jar`

Unanswered readings report `-` and drop the service cache so the next poll rebinds.

## Porting to Ioniq 5: what to establish first

Ioniq 5 is also Hyundai Gen5W, so much of this probably transfers — but **nothing
below is verified.** Treat every item as an open question.

1. **Android level and ABI.** Confirm API 19 / 32-bit ARM. A newer Gen5W build
   changes the signing requirements (v1-only may no longer be needed) and may not
   need `GET_TASKS`.
2. **Do the factory frameworks exist, with the same class and method names?**
   Check `/system/framework/automotive.jar` and
   `/system/framework/com.hkmc.ext.hcan.jar`. If a binder name differs, the guard
   reports `-` and fails closed — safe, but Plex stays permanently blocked. This
   is the single highest-risk area for the port; verify each of the four readings
   individually before trusting the package.
3. **Gear/speed encodings.** Confirm `getGearPStatus()` still uses the 0/1
   encoding the policy expects. A different encoding could silently read as
   "parked".
4. **Status-bar inset height.** The EV6 inset is 90 px at 1920×720. Ioniq 5 trim
   levels have different panels; the fullscreen patch may need a different value or
   none at all.
5. **Audio source behavior.** Confirm whether `AudioServiceHelper` auto-restores
   the previous source the same way. If not, the audio patch may be unnecessary.
6. **NEMESIS version.** Re-check the descriptor constraints against whatever
   version is installed.
7. **Compatibility gate.** Add a new profile rather than widening the existing one.

Suggested order: confirm framework/binder availability and encodings **before**
building any package. A guard that cannot read the vehicle is safe but useless,
and that is the most likely failure mode.

## Known unresolved Plex issues

- **"Sign in with Google" does not work.** The old client defers to a browser
  component this system lacks. Workaround is email + password. Fixing it likely
  means installing a browser or a WebView able to complete OAuth — untested, and
  the owner's stated next step.
- **Two-factor codes** have no field in this client: the password and the current
  six-digit code are concatenated as one string, no space.
- **Transcode quality should be set to 720p**; higher settings stutter or fail to
  start on this hardware.

## Honest status

- `1.1.0` is published but **has not itself been installed on a vehicle.** It is a
  byte-for-byte rebuild of the validated `compat-test` 0.1.3 with only the package
  identity and version strings changed. The car currently runs `0.1.3`.
- Owner-confirmed on the EV6: install from USB works, playback works, the FM radio
  regression is gone, Park → Reverse → Park restores the previous source, and Plex
  stops working once the car is moving.
- Still unmeasured: event-to-stop latency, reboot recovery, background/deep-link
  termination, no-collateral-kill confirmation. See `docs/device-validation.md`.
