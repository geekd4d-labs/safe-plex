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
bdd746d124a3efb3c86ca841c93ec5c2cae599b8c736ec66d96420b5971a3e7b  artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026-AUDIOSRC.apk
```

The APK is stored at `artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk` in this private repository. It was signed with the dedicated private `Aperture Plex Car Test` key. The key and password files must remain outside this repository.

## Guarded NEMESIS compatibility test

This separate NEMESIS test uses the parked-playback-tested `GET_TASKS`, current-CA, and fullscreen APK. Its NEMESIS package retains the standalone Park Guard.

```text
2022df4f069ee48e3a527ece0544ea234e28e2f6cfc10d90c632060f228f2119  dist/plex-compat-test-guarded-0.1.3-usb.zip
314c5e1f1357a536a8715073ce5092d7e189dcd5af5b97a23e8ac339212340a0  dist/plex.geekd4dlabs.compat-test.zip
```
