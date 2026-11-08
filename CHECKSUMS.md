# Reviewed inputs and validated private artifacts

## Inputs

```text
31b2d5312a0f81627c2831fc1bd376ba149583166d06dab281001a53b068ef0c  com.plexapp.android_6.17.1.5294_arm-v7a_minAPI16_apkmirror.apk
427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285  vendor/cacert-2026-11-05.pem
```

CA source: `https://curl.se/ca/cacert.pem`, Mozilla data dated 2026-11-05.

## Signed APKs

```text
bdd746d124a3efb3c86ca841c93ec5c2cae599b8c736ec66d96420b5971a3e7b  artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026-AUDIOSRC.apk
d44d56be3d15b07feb0c034663008c8997765b444b7065c81d1692f02fab239f  artifacts/Plex-6.17.1.5294-EV6-FULLSCREEN-CA2026.apk
```

`-AUDIOSRC` is the current production APK and the one shipped in SAFE PLEX
`1.1.0`. The earlier build without audio source retention is kept only for
comparison.

Both were signed with the dedicated private `Aperture Plex Car Test` key.
Signer certificate SHA-256:

```text
b7c45789ad339affaecd51ef6be24c63786df75e9c273ac951b1cd1d755c2be0
```

The keystore and password files must remain outside this repository.

## SAFE PLEX 1.1.0 (production NEMESIS package)

```text
a18d3c0e9b04444c78728ddf0ffad9d5c3e175420a78f9547820fc63b99b6a8a  dist/safe-plex-1.1.0-usb.zip
21fc4dc7554073b9a5298e46150ed011ea6f092a14f0e76769c1586416687e63  dist/plex.geekd4dlabs.safe.zip
c454db0e2c41d990bc4679893310286a5fc14b02e34744bbc810f5cd52d25a3c  safeplex-guard.jar
```

## Retired artifacts

Superseded by 1.1.0 and kept for provenance only:

```text
2022df4f069ee48e3a527ece0544ea234e28e2f6cfc10d90c632060f228f2119  plex-compat-test-guarded-0.1.3-usb.zip
314c5e1f1357a536a8715073ce5092d7e189dcd5af5b97a23e8ac339212340a0  plex.geekd4dlabs.compat-test.zip
```
