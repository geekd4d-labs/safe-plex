# SAFE PLEX for Kia/Hyundai Gen5W

> [!CAUTION]
> **PARKED USE ONLY.** SAFE PLEX is designed only for a fully stopped vehicle in Park. Video use may be restricted or illegal in your jurisdiction, including where this was developed. Do not remove, weaken, or bypass its Park safeguards. You are responsible for lawful and safe use.

Plex Android `6.17.1.5294`, patched for compatible Kia/Hyundai Gen5W head units (Android 4.4.2 / API 19), packaged for NEMESIS with an independent fail-closed Park Guard.

**Current release: `1.2.1`** — one package, `plex.geekd4dlabs.safe`, named **SAFE PLEX**. The HMG-API variant is retired (see [Retired variants](#retired-variants)).

**Safety status:** the APK and guard behavior come from the `0.1.3` lineage physically exercised on a 2022 US Kia EV6; the `1.2.1` NEMESIS archive has not itself been installed on a vehicle. Ioniq 5 and other Gen5W vehicles are experimental until owner testing confirms both the availability and meaning of their factory telemetry. Missing, throwing, malformed, or unreadable calls fail closed, but a different vehicle could return plausible values with different meanings; physical Park/Reverse/Drive validation is therefore required. EV6 checks are tracked in `docs/device-validation.md`.

## How it works

SAFE PLEX is two things shipped together: a Plex build patched to work on this old head unit, and a root service that decides when Plex is allowed to run.

### The Park Guard

A root service, `safe-plex-guard`, supervises Plex for the life of the head unit session. It reads the car's own factory vehicle services directly over binder — the same calls the stock video gate uses — and asks four questions:

| Reading | Required value |
| --- | --- |
| `gear.park` | `1` (in Park) |
| `moving` | `0` (not moving) |
| `speed` | `abs(speed) <= 0.5 km/h` |
| `driving.restricted` | `0` (no restriction) |

Plex is permitted only after **all four** hold true continuously for 1.5 seconds. That debounce stops a brief stop-and-go from flickering Plex back to life.

The guard is **fail-closed**, which is the important part: it does not look for proof that the car is moving, it demands proof that the car is parked. Anything less blocks Plex — a missing reading, a malformed value, two readings that contradict each other, data older than the freshness window, or vehicle services that have not answered yet after boot. A guard that cannot read the car assumes the car is dangerous.

While Plex is blocked, the guard issues `am force-stop com.plexapp.android` once per second, and falls back to an exact-match `/proc` scan to kill Plex child processes. Matching is exact — `com.plexapp.android` and its `com.plexapp.android:` children only — so it never kills a bystander app. The guard starts blocked, and it never writes to vehicle state; its only power is stopping one app.

Guard state is observable at `/data/local/safe-plex/state`.

### The Plex compatibility patches

The upstream APK is modified as little as possible — only what this firmware actually requires:

1. **`android.permission.GET_TASKS`** — required by this OEM firmware even when Plex calls `Activity.finish()`.
2. **Current CA bundle** — Plex's embedded 2011 certificate authorities are replaced with reviewed Mozilla CA data dated 2026-11-05, which clears `libcurl` certificate error 60 and lets Plex authenticate over HTTPS. Certificate verification stays **enabled**.
3. **`FLAG_FULLSCREEN`** on both mobile video-player activities, so Gen5W drops its 90-pixel status-bar inset. This removes the inset only — video is never zoomed, stretched, or cropped, so 16:9 stays 16:9 on the wider 1920×720 display.
4. **Audio source retention** — see below.
5. **A stable owner-controlled signing identity**, Android 4.4-compatible v1 signing. Reusing the same key means updates install in place and preserve your Plex login.

### Why audio source retention is needed

Stock Plex abandons Android audio focus the moment a player stops. The Gen5W `AudioServiceHelper` treats that as "nothing is playing" and auto-restores the previous AV source — so the FM radio screen pops up over Plex whenever you stop a video.

A stopping player now hands focus to a process-wide no-op holder *before* releasing its own listener, so the head unit still sees Plex as the active source. A released listener ignores the focus loss the holder causes, and a new playback request re-arms it.

This does not weaken the guard. A guard force-stop kills the whole Plex process, so Android releases the holder automatically and the head unit returns to its normal source.

## Plex quirks on this head unit

Things that are not bugs in SAFE PLEX, but will bite you on a 2014-era Android client.

### Sign in with a Plex account, not Google

**"Sign in with Google" does not work yet.** This old client hands Google auth off to a browser component this system does not provide. Use the email-and-password form.

Getting Google auth working likely means installing a browser or a WebView capable of completing the OAuth flow — unresolved and untested.

### Two-factor codes go on the end of your password

This client has no field for a 2FA code. Plex's legacy format expects the password and the current six-digit code concatenated as a single string, no space.

If your password is `NobodyWillGuessThisPassword` and your code is `123456`, enter:

```text
NobodyWillGuessThisPassword123456
```

The code expires quickly, so have it ready before you tap the field.

### Set transcode quality to 720p

For the smoothest playback, set your Plex transcode quality to **720p**. Higher settings stutter or fail to start on this hardware. The display is 1920×720, so 720p is not costing you meaningful detail.

## Install

Download `safe-plex-1.2.1-usb.zip` from the release, extract it to the root of a FAT32 USB stick so the stick contains:

```text
Packages/plex.geekd4dlabs.safe.zip
NEMESIS.data
README.txt
```

Insert the stick and install **SAFE PLEX** through NEMESIS, parked.

> [!IMPORTANT]
> **Connect the head unit to Wi-Fi through NEMESIS before using Plex.** Open NEMESIS Manager, tap **WiFi**, and join a network (home Wi-Fi or a phone hotspot). Plex needs this network connection to sign in and stream; without it, Plex will not work.

Requirements: NEMESIS installed and working with an active Wi-Fi connection; Kia/Hyundai Gen5W Android 4.4.2 / API 19, 32-bit ARM; factory frameworks `/system/framework/automotive.jar` and `/system/framework/com.hkmc.ext.hcan.jar` present. Marketplace metadata marks the physically exercised EV6 260507 firmware as a full match; other CVEV firmware and US Ioniq 5 NEEV/NEEV23 model families are partial/experimental matches. Other model families are incompatible unless the user explicitly accepts NEMESIS's risk override. Missing or unreadable factory calls leave the guard blocked. Plausible readings with different vehicle-specific meanings cannot be detected automatically, so every new model/firmware needs physical gear-state validation.

### Upgrading from the test package

If `PLEX COMPAT TEST (GUARDED)` (`plex.geekd4dlabs.compat-test`) is installed, **uninstall it through NEMESIS first.** Both own `com.plexapp.android`, and two concurrent guards make uninstall and process control ambiguous. Uninstalling clears Plex app data, so you will sign in again.

## Build

Requirements: Python 3.9+, Java 17+, Apktool 3.0.3, Android build-tools 36.0.0.

Patch and sign the APK:

```bash
./scripts/build.sh \
  --apk /private/path/com.plexapp.android_6.17.1.5294_arm-v7a_minAPI16_apkmirror.apk \
  --apktool /private/path/apktool_3.0.3.jar
```

`scripts/patch_decoded.py` applies every compatibility change to a decoded tree and is idempotent, so re-running it is safe. Sign with the dedicated private key via `scripts/sign.sh`; Android 4.4 requires the v1 signature.

Test and build the package:

```bash
python3 tools/test_all.py
python3 tools/build_safe_plex.py
```

Outputs:

```text
dist/safe-plex-1.2.1-usb.zip        USB-root archive
dist/plex.geekd4dlabs.safe.zip      inner NEMESIS package
dist/SHA256SUMS-safe-plex.txt
dist/VERIFICATION-safe-plex.json
```

The builder refuses APK bytes that do not match the reviewed SHA-256, and verifies the package name, version, API level, ABI, launcher activity, signing certificate, guard dex JAR, nested USB archive, and descriptor. Archives are byte-for-byte reproducible.

### NEMESIS descriptor constraints

The live NEMESIS parser is stricter than its documentation. Both cost a release to learn:

- The package descriptor uses `types=` (plural). The USB root descriptor uses singular `type=install`.
- `short-desc` **must be 64 characters or fewer**, or the entire install fails with `invalid package metadata`.
- The USB root descriptor must be named exactly `NEMESIS.data`.

A USB install failure writes its reason to `/data/nemesis/logs/usb-handler/usb-handler.log`, not `/data/nemesis/nemesis.log`.

## Repository layout

```text
package/      production NEMESIS profile (descriptors, guard scripts, README)
service/      Park Guard Java source and host tests
scripts/      APK patch, build, and sign tooling
tools/        package builders and contract tests
tests/        patcher unit tests
artifacts/    reviewed signed APKs
docs/         vehicle validation records
vendor/       reviewed CA bundle
```

## Physical validation

Confirmed on the target 2022 US Kia EV6:

- Plex installs via NEMESIS from USB, launches, authenticates, and plays video
- Correct 16:9 aspect ratio and full-height player
- Updated CA bundle clears `libcurl` certificate error 60
- Pausing or stopping playback no longer switches the head unit to FM radio, and the AV source stays `com.plexapp.android`
- Park → Reverse → Park returns the head unit to its previous source
- **Plex stops working once the car is moving**

Remaining checks — measured event-to-stop latency, reboot recovery, background/deep-link termination, and no-collateral-kill confirmation — are tracked in `docs/device-validation.md`.

## Retired variants

- **HMG-API mod** — removed at `1.1.0`. It required HMG-API `1.0.2` and a narrowly gated internal vehicle socket. The NEMESIS package supersedes it and needs no HMG-API.
- **`plex.geekd4dlabs.compat-test`** — the guarded test identity used through `0.1.3`. Its code is what shipped as `1.1.0` under the production name.

Retired code remains in git history.

## Provenance and licensing

- Plex is proprietary to Plex, Inc.; see `NOTICE.md`. Keep this repository private and do not redistribute the APK. Signing keys, passwords, MFA codes, Plex tokens, app data, and device logs are not committed.
- The Park Guard is adapted from the physically validated private SAFE VLC implementation at commit `2953cf3d2021ecb7022c02992f335fcf2521cf7b`.
- HMG-API (retired dependency): https://github.com/VysseCodes/HMG-API, AGPL-3.0.
- SAFE PLEX guard source: AGPL-3.0-or-later.
