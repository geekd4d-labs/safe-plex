# Reviewed inputs and validated private artifacts

## Inputs

```text
31b2d5312a0f81627c2831fc1bd376ba149583166d06dab281001a53b068ef0c  com.plexapp.android_6.17.1.5294_arm-v7a_minAPI16_apkmirror.apk
427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285  vendor/cacert-2026-11-05.pem
```

CA source: `https://curl.se/ca/cacert.pem`, Mozilla data dated 2026-11-05.

## Vehicle-tested private build

```text
d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f  artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk
```

The APK is stored at `artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk` in this private repository. It was signed with the dedicated private `Aperture Plex Car Test` key. The key and password files must remain outside this repository.

## Guarded NEMESIS compatibility test

This separate NEMESIS test uses the parked-playback-tested `GET_TASKS`, current-CA, and fullscreen APK. Its NEMESIS package retains the standalone Park Guard.

```text
75d5c9239e2ad64f4993a5c78660e6afc60f6ba21366da7a8ca80999d9e944a1  dist/plex-compat-test-guarded-0.1.2-usb.zip
76b77523c3ed7707b65e4dfbd3fd395baf605e84f6cab86795488d8d85475848  dist/plex.geekd4dlabs.compat-test.zip
```
