# Reviewed inputs and validated private artifacts

## Inputs

```text
31b2d5312a0f81627c2831fc1bd376ba149583166d06dab281001a53b068ef0c  com.plexapp.android_6.17.1.5294_arm-v7a_minAPI16_apkmirror.apk
427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285  vendor/cacert-2026-11-05.pem
```

CA source: `https://curl.se/ca/cacert.pem`, Mozilla data dated 2026-11-05.

## Vehicle-tested private build

```text
d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f  Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk
```

The APK itself is deliberately excluded from Git. It was signed with the dedicated private `Aperture Plex Car Test` key. The key and password files must remain outside this repository.
