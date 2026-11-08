# SAFE PLEX for Kia/Hyundai Gen5W

> [!CAUTION]
> **PARKED USE ONLY.** SAFE PLEX is designed only for a fully stopped vehicle in Park. Video use may be restricted or illegal in your jurisdiction, including where this mod was developed. Do not remove, weaken, or bypass its Park safeguards. You are responsible for lawful and safe use.

Private Plex Android `6.17.1.5294` compatibility build and HMG-API Park Guard for the 2022 US Kia EV6 Gen5W head unit (Android 4.4.2 / API 19).

**Safety status:** the independent fail-closed guard and HMG package are implemented, installed on the vehicle, and host-verified. The Plex compatibility APK has been exercised on the physical car while parked, and the guard has been physically confirmed to kill Plex on both Park → Reverse and Park → Drive. The remaining physical matrix (launch-while-unsafe survival, background/deep-link termination, head-unit reboot recovery, measured event-to-stop latency, and no-collateral-kill confirmation) is tracked in `docs/device-validation.md` before SAFE PLEX can be called fully vehicle-validated.

## Safety architecture

SAFE PLEX uses two independent layers:

1. HMG-API `not_while_driving`, which follows the head unit's stock driving regulation and popup.
2. A separate root `safe-plex-guard` service. It permits Plex only after `gear.park=1`, `moving=0`, `abs(speed)<=0.5 km/h`, and `driving.restricted=0` remain valid for 1.5 seconds. Unsafe, contradictory, malformed, missing, or stale readings immediately block Plex. While blocked, the guard repeats `am force-stop com.plexapp.android` once per second and has an exact-package `/proc` kill fallback for Plex child processes.

The guard reads exactly those four compile-time telemetry names from HMG-API 1.0.2's root-peer-only internal vehicle socket. It returns after all four exact lines arrive rather than waiting for EOF, avoiding the physically observed three-second public-client EOF timeout. This path bypasses `hmgapid` declaration checks and request audit logging, so the descriptor remains narrowly gated and later HMG versions require physical validation. An incompatible protocol fails closed.

## Plex compatibility changes

The reviewed upstream APK is patched to:

1. Add `android.permission.GET_TASKS`, required by this OEM firmware even when Plex calls `Activity.finish()`.
2. Replace Plex's 2011 embedded CA bundle with reviewed Mozilla CA data dated 2026-11-05. Certificate verification remains enabled.
3. Add `FLAG_FULLSCREEN` to both Plex mobile video-player activities so Gen5W removes its 90-pixel status-bar inset.
4. Use a stable owner-controlled Android 4.4-compatible app signature.

It does **not** zoom, stretch, or crop video. A 16:9 picture remains 16:9 on the wider 1920×720 display.

## Compatibility gate

The HMG mod intentionally accepts only:

- Model: `CVEV`
- Region: `USA`
- Firmware: `260507`
- HMG-API: exactly `1.0.2`, whose internal vehicle protocol is the reviewed and Safe-VLC-validated baseline
- Android: Gen5W Android 4.4.2 / API 19

Do not loosen this gate for another vehicle or firmware. Add and physically validate a separate profile.

## Private APK

The exact parked-playback-tested build is committed for authorized repository members:

```text
artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk
artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026-AUDIOSRC.apk
SHA-256: d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f
```

Keep this repository private; do not redistribute the APK. The unmodified upstream APK, signing keys, passwords, MFA codes, Plex tokens, app data, device screenshots, and logs are not committed.

## Build the Plex compatibility APK

Requirements: Python 3.9+, Java 17+, and Apktool 3.0.3.

```bash
./scripts/build.sh \
  --apk /private/path/com.plexapp.android_6.17.1.5294_arm-v7a_minAPI16_apkmirror.apk \
  --apktool /private/path/apktool_3.0.3.jar
```

Sign with the dedicated private key using `scripts/sign.sh`. Android 4.4 requires the v1 signature; same-key updates preserve Plex authentication and app data.

## Build the compatibility-only test archive

The repository also defines a deliberately separate **bench/emulator-only** test artifact. It contains the reviewed Plex compatibility APK, its checksum, and test instructions—but no HMG-API package, NEMESIS installer, vehicle service, or Park Guard.

```bash
python3 tools/build_compat_test.py
```

Output:

```text
dist/compat-test/Plex-6.17.1.5294-EV6-COMPAT-TEST-1.zip
```

This is not an in-car SAFE PLEX release and must not replace either guarded distribution. Its archive structure is deterministic and the builder refuses APK bytes that do not match the reviewed SHA-256.

## Build the guarded NEMESIS compatibility test

For physical head-unit testing, a separate NEMESIS package uses the established Plex compatibility APK—`GET_TASKS`, the current CA bundle, fullscreen player flags, audio source retention, and the stable private signature. Because it installs on a vehicle, it retains the independent standalone Park Guard; it has no HMG-API dependency.

```bash
python3 tools/build_compat_nemesis.py
```

Ready-to-extract USB archive:

```text
dist/plex-compat-test-guarded-0.1.3-usb.zip
SHA-256: 2022df4f069ee48e3a527ece0544ea234e28e2f6cfc10d90c632060f228f2119
```

The inner NEMESIS package is `Packages/plex.geekd4dlabs.compat-test.zip`. Do not install it alongside the HMG-API SAFE PLEX mod or the regular standalone SAFE PLEX package: all variants own `com.plexapp.android`, and concurrent guards or package managers create ambiguous uninstall and process-control behavior. Remove the previous variant through its own manager first.

## Test and build the HMG mod

Prerequisites:

- Exact clean HMG-API commit `180185de2c57afb2cca4858d0be7828e8f1051d6`
- JDK 17
- Android SDK platform and build-tools 36.0.0
- Established HMG author key and paired `.pub` file outside this repository

```bash
python3 tools/test_all.py
python3 tools/build_mod.py \
  --hmg-source /opt/data/projects/Ev6/HMG-API \
  --author-key /opt/data/private-keys/safe-vlc/author.key
```

Outputs:

- `dist/geekd4dlabs-safe-plex-0.1.0.zip` — signed HMG mod
- `dist/geekd4dlabs-safe-plex-0.1.0-usb.zip` — USB-root archive
- `dist/VERIFICATION.json`
- `dist/SHA256SUMS.txt`

The builder verifies the Plex APK's package, version, API, ABI, launcher, app-signing certificate, exact bytes, service dex JAR, HMG signature, nested USB archive, and descriptor.

## Current physical validation

Verified while parked on the target EV6:

- Plex installs and launches
- Account login works using Plex's legacy MFA format (`password` followed immediately by the current six-digit code)
- Library access and video playback work
- Correct 16:9 aspect ratio and full-height player
- Updated CA bundle removes `libcurl` certificate error 60

Verified on the physical EV6 with the Park Guard installed:

- Shifting Park → Reverse kills Plex
- Shifting Park → Drive kills Plex

The HMG guard package is **host-built and structurally verified, and the two primary gear-transition kill paths are now physically confirmed**. Remaining vehicle checks (launch-while-unsafe survival, background/deep-link termination, reboot recovery, measured latency, and no-collateral-kill confirmation) are tracked in `docs/device-validation.md`.

## Provenance and licensing

- Plex is proprietary to Plex, Inc.; see `NOTICE.md`.
- The Park Guard is adapted from the physically validated private SAFE VLC implementation at commit `2953cf3d2021ecb7022c02992f335fcf2521cf7b`.
- HMG-API: https://github.com/VysseCodes/HMG-API, AGPL-3.0.
- SAFE PLEX guard source: AGPL-3.0-or-later.
