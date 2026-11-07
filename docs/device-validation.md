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

## Implemented and host-verified

- [x] Independent root supervisor starts fail-closed
- [x] Safe policy requires Park, not moving, near-zero finite speed, and unrestricted state
- [x] Safe transition requires a 1.5-second debounce
- [x] Stale, invalid, contradictory, malformed, or unavailable telemetry blocks Plex
- [x] Enforcement repeats once per second while blocked
- [x] Primary enforcement uses `am force-stop com.plexapp.android`
- [x] Bounded timeout falls back to exact package/child-process matching under `/proc`
- [x] Factory `not_while_driving` remains a second layer
- [x] Service compiles and dexes for API 19
- [x] Signed HMG archive and nested USB archive verify recursively
- [x] Packaged Plex APK bytes match the parked-playback-tested artifact

## Required physical tests before calling it SAFE PLEX

The independent HMG supervisor starts blocked and permits playback only when fresh, valid telemetry proves all of the following:

- `gear.park == 1`
- `moving == 0`
- finite absolute speed is within a documented near-zero tolerance
- `driving.restricted == 0`

Missing, malformed, contradictory, stale, or unavailable telemetry is unsafe. Unsafe state must immediately and repeatedly force-stop `com.plexapp.android`, including its services and exact child processes. Keep HMG's stock `not_while_driving` restriction as a second layer.

Physical acceptance tests:

- [x] Park → Reverse stops visible playback
- [x] Park → Drive stops visible playback
- [ ] Launch while already in Reverse/Drive cannot survive
- [ ] Background playback is terminated after shifting out of Park
- [ ] File/deep-link launch is terminated while out of Park
- [x] HMG vehicle-service loss terminates a running Plex process and repeated launch attempts remain blocked
- [x] Restoring fresh Park telemetry permits Plex again after the safe-state debounce
- [x] Supervisor restart begins blocked, stops Plex in 2.2 seconds on this head unit, then permits relaunch only after fresh Park telemetry debounces
- [ ] Head-unit reboot recovers fail-closed
- [ ] Park → Reverse/Drive event-to-stop latency is measured from device timestamps
- [ ] No unrelated package/process is killed during the physical shift tests

Installed artifact:

```text
geekd4dlabs-safe-plex 0.1.0
HMG author key: 96f22dc5-6d6e-8098-bbc9-e554834eb78d
Mod SHA-256: c1e917476bac28e3fa728ac996bf70d3cf16844928c4c0e624cd4be851014f6b
```

Remaining gaps before calling the gear-transition matrix complete: cannot-survive launch while already in Reverse/Drive, background/deep-link playback after shifting out of Park, head-unit reboot recovery, measured event-to-stop latency, and confirmation no unrelated process is affected during the shift tests.
