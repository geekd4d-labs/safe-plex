# Safe Plex for Kia/Hyundai Gen5W

Private, reproducible compatibility patches for Plex Android `6.17.1.5294` on the 2022 US Kia EV6 Gen5W head unit (Android 4.4.2 / API 19).

> **Safety status:** playback works while parked, but the independent HMG Park Guard is **not implemented yet**. Do not use video while the vehicle is moving. The intended release gate is fail-closed enforcement that force-stops `com.plexapp.android` unless fresh vehicle telemetry explicitly confirms Park.

## What this fixes

The reviewed upstream APK is preserved outside Git and pinned by SHA-256. The build pipeline makes four scoped changes:

1. Adds `android.permission.GET_TASKS`, required by this OEM firmware even when Plex calls `Activity.finish()`.
2. Replaces Plex's 2011 embedded CA bundle with reviewed Mozilla CA data dated 2026-11-05. Certificate verification remains enabled.
3. Adds `FLAG_FULLSCREEN` to both Plex mobile video-player activities so Gen5W removes its 90-pixel status-bar inset.
4. Re-signs the private build with a stable owner-controlled key using an Android 4.4-compatible v1 signature.

It does **not** zoom, stretch, or crop video. A 16:9 picture remains 16:9 on the wider 1920×720 display.

## Repository boundaries

Not committed:

- Plex APKs or decompiled Plex source/resources
- Signing keys or password files
- Plex passwords, MFA codes, account tokens, or app data
- Device screenshots and logs

See `NOTICE.md` and `.gitignore`.

## Reviewed input

Supply the original standalone ARMv7 APK yourself:

```text
Plex 6.17.1.5294
package: com.plexapp.android
minSdk: 16
SHA-256: 31b2d5312a0f81627c2831fc1bd376ba149583166d06dab281001a53b068ef0c
```

The build refuses any other upstream digest.

## Build

Requirements:

- Python 3.9+
- Java 17+
- Apktool 3.0.3

```bash
./scripts/build.sh \
  --apk /private/path/com.plexapp.android_6.17.1.5294_arm-v7a_minAPI16_apkmirror.apk \
  --apktool /private/path/apktool_3.0.3.jar
```

The unsigned result is written under `dist/` by default.

## Sign

Keep the dedicated keystore and its password files outside the repository.

```bash
./scripts/sign.sh \
  --apk dist/Plex-6.17.1.5294-EV6-unsigned.apk \
  --out dist/Plex-6.17.1.5294-EV6-signed.apk \
  --build-tools "$ANDROID_HOME/build-tools/36.0.0" \
  --keystore "$HOME/hmg-private/keys/plex-car-test.p12" \
  --alias plex-car-test \
  --store-pass-file "$HOME/hmg-private/keys/plex-car-test.pass" \
  --key-pass-file "$HOME/hmg-private/keys/plex-car-test-key.pass"
```

Android 4.4 validates the v1 signature. Same-key updates preserve Plex authentication and app data.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

For a physical playback session, dump the UI hierarchy and verify the video surface uses the full 720-pixel display height:

```bash
python3 tests/assert_video_fullscreen.py playback-ui.xml
```

## Current physical validation

Verified on the target EV6 while parked:

- Installation and launch
- Plex account login with Plex's legacy MFA format (`password` followed immediately by the current six-digit code)
- Library access
- Video playback
- Correct 16:9 aspect ratio
- Full-height player with the OEM top bar removed
- Updated CA bundle with no `libcurl` error 60

Not yet validated or implemented:

- HMG packaging
- Strict Park-only supervisor
- Park → Reverse/Drive shutdown latency
- Background-playback termination
- Telemetry-loss fail-closed behavior
- Reboot/recovery validation

See `docs/device-validation.md` for the acceptance gate.
