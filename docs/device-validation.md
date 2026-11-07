# Device validation and safety gate

Target: 2022 US Kia EV6 Gen5W, Android 4.4.2, 1920×720 display.

## Completed while parked

- [x] Original APK identity and SHA-256 verified
- [x] Patched APK v1 signature verified
- [x] Package installs and launches
- [x] `GET_TASKS` OEM crash eliminated
- [x] Current Plex account login succeeds with legacy MFA concatenation
- [x] Plex library opens
- [x] Video plays with audio
- [x] Video retains its source aspect ratio
- [x] Playback activity removes the OEM top status bar/inset
- [x] Updated CA bundle removes `libcurl` certificate error 60

## Required before calling it Safe Plex

The independent HMG supervisor must start blocked and permit playback only when fresh, valid telemetry proves all of the following:

- `gear.park == 1`
- `moving == 0`
- finite absolute speed is within a documented near-zero tolerance
- `driving.restricted == 0`

Missing, malformed, contradictory, stale, or unavailable telemetry is unsafe. Unsafe state must immediately and repeatedly force-stop `com.plexapp.android`, including its services and exact child processes. Keep HMG's stock `not_while_driving` restriction as a second layer.

Physical acceptance tests:

- [ ] Park → Reverse stops visible playback
- [ ] Park → Drive stops visible playback
- [ ] Launch while already unsafe cannot survive
- [ ] Background playback is terminated
- [ ] File/deep-link launch is terminated
- [ ] Telemetry loss terminates playback and remains blocked
- [ ] Supervisor restart and head-unit reboot recover fail-closed
- [ ] Event-to-stop latency is measured from device timestamps
- [ ] No unrelated package/process is killed

Until every item above is evidenced on the physical vehicle, this repository is a compatibility build—not a completed driving-safety control.
