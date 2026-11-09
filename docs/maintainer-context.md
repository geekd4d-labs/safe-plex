# SAFE PLEX maintainer context

This checkpoint is the durable handoff for future Hermes chats and maintainers.
Use the repository history and current release assets for exact bytes and hashes.

## Project

- Repository: private GitHub repository `geekd4d-labs/safe-plex`
- Local path: `/opt/data/projects/Ev6/safe-plex`
- Package ID: `plex.geekd4dlabs.safe`
- Current package release: `1.2.1`
- GitHub release: `https://github.com/geekd4d-labs/safe-plex/releases/tag/v1.2.1`
- NEMESIS Package Store submission has **not** been performed.
- Keep the repository private unless Ryan explicitly authorizes a visibility
  change.

## Current release state

`v1.2.1` is a NEMESIS Package Store candidate. The tag points to commit
`bf08ad31a6e89c37ffb13e12204cb9e8e3bae60c`, which contains the final concise
Marketplace description. The 1.2.1 assets were refreshed after publication to
make that metadata-only correction; files downloaded before the refresh are
stale.

Published candidate hashes:

- Store upload `plex.geekd4dlabs.safe-1.2.1.zip`:
  `f00264249c0e4518c72ae79b04478ed54737f94024fcdc31a8aa9439feac14db`
- USB installer `safe-plex-1.2.1-usb.zip`:
  `204a70d7ba793f44ec791aaf821180426a52c828775edd6aa64b1dea316dd3f3`
- Checksum manifest:
  `44f8268d0a9419f8efb3f8c4125213d8e73e1c9ca00642a6ecb9652a4aaf5431`
- Verification JSON:
  `a03de585d6a9fea8b0ddc837d5ff625ec01b97231ba7d807ad04b3875a0370b6`

The Store upload is the **inner** ZIP with `NEMESIS.data` at its root. The USB
ZIP is for installing/testing in a vehicle.

## Marketplace descriptor decisions

`package/src/NEMESIS.data` intentionally contains:

```ini
version=1.1
id=plex.geekd4dlabs.safe
name=SAFE PLEX
type=application,service
types=application,service
package-version=1.2.1
depends=!plex.geekd4dlabs.compat-test
os=CVEV.USA.0000.V015.012.260507
models=cvev_us,neev_us,neev23_us
```

- Descriptor `version=1.1` is the NEMESIS metadata schema, not the SAFE PLEX
  package version.
- Keep canonical `type=` and the identical legacy `types=` fallback.
- Exact EV6 firmware `CVEV.USA.0000.V015.012.260507` is full/green.
- Other `cvev_us` firmware and US Ioniq 5 `neev_us` / `neev23_us` are
  partial/yellow and experimental.
- Other model families are incompatible/red.
- The conflict prevents coexistence with the retired compatibility-test package.
- The concise `detailed-desc` must retain fail-closed Park Guard, experimental
  Ioniq 5, and parked-use warnings. Ryan explicitly requested that it omit
  `0.1.3 runtime` and `archive is not vehicle-installed` wording.

## Safety boundary

Never weaken these rules:

- Start blocked and require positive proof of Park.
- Require Park, not moving, finite near-zero speed, and unrestricted state.
- Missing, throwing, malformed, contradictory, stale, or unreadable factory
  telemetry blocks Plex.
- Match only `com.plexapp.android` and its colon-suffixed child processes.
- Plausible values with different vehicle-specific semantics cannot be detected
  automatically; every new vehicle/firmware needs physical Park/Reverse/Drive
  validation.

The APK and guard behavior descend from the `compat-test` 0.1.3 runtime lineage
physically exercised on Ryan's 2022 US Kia EV6. The exact 1.2.1 candidate
archive has not yet been installed on a vehicle. Preserve that distinction in
README, validation records, and release notes, but not in the concise Store long
description.

## Documentation decisions

- The top-level `README.md` says the head unit must connect to Wi-Fi through
  NEMESIS Manager before Plex can sign in or stream.
- Do **not** add that Wi-Fi wording to `package/README.txt` until a future
  version-bumped package release.
- A repository README-only correction gets committed and pushed without a
  package version bump or rebuilt release.

## Verification already completed

For the final refreshed 1.2.1 candidate:

- `python3 tools/test_all.py` passed.
- Two full builds produced byte-identical inner and USB archives.
- The current upstream NEMESIS `make_nemesis_package.py` accepted the emitted
  inner package.
- Published assets were downloaded and compared byte-for-byte with the local
  build.
- Published `NEMESIS.data` was read back and checked for the concise description.

## Remaining work before Store submission

1. Connect the EV6/head unit over ADB.
2. Run `nemesis pkg-info` against the exact inner candidate and require parsed
   metadata plus `compat=full`.
3. Install, use, and uninstall the exact 1.2.1 candidate on the head unit.
4. Physically verify Park -> Reverse/Drive blocks or stops Plex, then Park allows
   it again only after the normal debounce.
5. Verify uninstall restores the unit and removes Plex, the guard service, and
   `/data/local/safe-plex`.
6. Record the evidence in `docs/device-validation.md`.
7. Submit to the NEMESIS Package Store only after Ryan explicitly authorizes it.

Ioniq 5 remains experimental until owner reports confirm factory-call behavior
and physical gear-state enforcement. Do not turn those reports into a full
support claim without sufficient evidence.

## Build and recovery commands

```bash
cd /opt/data/projects/Ev6/safe-plex
python3 tools/test_all.py
python3 tools/build_safe_plex.py

gh release view v1.2.1
gh release download v1.2.1 --dir /path/to/verification-directory
```

For a package-changing release, build twice and compare both
`dist/plex.geekd4dlabs.safe.zip` and `dist/safe-plex-<version>-usb.zip`. Inspect
the emitted nested descriptor, not just the source template. After publishing,
verify branch SHA, tag SHA, release target, all asset digests, and downloaded
bytes before reporting success.
