# Plex 6.17.1.5294 compatibility test

## BENCH / EMULATOR ONLY

This archive contains the vehicle-tested legacy Plex compatibility APK but **no vehicle installer**, HMG-API package, NEMESIS package, or background vehicle service. It does not contain a Park Guard or any other independent motion lockout.

Use it only on an Android 4.4/API-19 bench head unit, emulator, or other non-vehicle test device. It is not an in-car SAFE PLEX release and must not replace either guarded SAFE PLEX distribution.

The APK contains only the established compatibility changes:

- OEM `GET_TASKS` compatibility permission
- Current embedded Mozilla CA bundle
- Fullscreen player window flags while preserving source aspect ratio
- Stable owner-controlled test signature

Package: `com.plexapp.android`

Launcher: `com.plexapp.plex.activities.SplashActivity`

APK SHA-256:

```text
d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f
```

This private test build contains proprietary Plex software. Do not redistribute it publicly. Never include Plex passwords, MFA codes, tokens, account data, or private signing material in test reports.
