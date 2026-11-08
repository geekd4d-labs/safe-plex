# Device validation and safety gate

Target: 2022 US Kia EV6 Gen5W, Android 4.4.2, 1920×720 display.
Physically exercised package lineage: `plex.geekd4dlabs.compat-test` `0.1.3`.
Current host-built package: `plex.geekd4dlabs.safe` (SAFE PLEX) `1.2.0`.

`1.2.0` has not itself been installed on a vehicle. Its reviewed Plex APK,
Park Guard behavior, guard scripts, and safety policy carry forward from the
physically exercised `0.1.3` lineage. Package identity, version, descriptor
metadata, and documentation differ, so the checks below must not be read as a
claim that the `1.2.0` archive itself was physically validated.

Items marked **[owner]** were confirmed by the vehicle owner in the car. Items
without that tag were verified from host tooling or device logs.

## Confirmed on the vehicle

Compatibility, while parked:

- [x] Original APK identity and SHA-256 verified
- [x] Patched APK v1 signature verified
- [x] Installs via NEMESIS from a USB stick and launches **[owner]**
- [x] `GET_TASKS` OEM crash eliminated
- [x] Plex account login succeeds using legacy MFA concatenation
- [x] Plex library opens
- [x] Video plays with audio
- [x] Video retains its source aspect ratio
- [x] Playback activity removes the OEM top status bar/inset
- [x] Updated CA bundle removes `libcurl` certificate error 60
- [x] Pausing or stopping playback no longer restores FM radio; `ModeManagerService`
      reports `isAvModePackage : com.plexapp.android` after Stop
- [x] Park → Reverse → Park returns the head unit to its previous source **[owner]**

Park Guard enforcement:

- [x] Park → Reverse stops visible playback
- [x] Park → Drive stops visible playback
- [x] Plex stops working once the car is moving **[owner]**
- [x] Vehicle-service loss terminates a running Plex process, and repeated launch
      attempts remain blocked
- [x] Restoring fresh Park telemetry permits Plex again after the safe-state debounce
- [x] Supervisor restart begins blocked, stops Plex in 2.2 seconds on this head unit,
      then permits relaunch only after fresh Park telemetry debounces

## Host-verified

- [x] Independent root supervisor starts fail-closed
- [x] Safe policy requires Park, not moving, near-zero finite speed, and unrestricted state
- [x] Safe transition requires a 1.5-second debounce
- [x] Stale, invalid, contradictory, malformed, or unavailable telemetry blocks Plex
- [x] Enforcement repeats once per second while blocked
- [x] Primary enforcement uses `am force-stop com.plexapp.android`
- [x] Bounded timeout falls back to exact package/child-process matching under `/proc`
- [x] Telemetry mapping is fail-closed: any missing or throwing reading reports `-`
      and blocks (16 host cases, including the 0/1 policy-encoding contract)
- [x] Guard jar compiles to a single deterministic `classes.dex`
- [x] NEMESIS descriptor contract: app + root service, correct paths, `restart` mode
- [x] Descriptor satisfies the live parser: `types=` plural, `short-desc` ≤ 64 chars
- [x] Guard script: API 19 + vehicle-framework preflight, boot-id/pid double-start
      lock, `cleanup` force-stops Plex
- [x] NEMESIS package and nested USB archive verify recursively; ZIP bytes deterministic
- [x] Shell scripts ship with LF line endings only
- [x] Packaged Plex APK bytes match the vehicle-tested artifact
- [x] Audio focus holder is process-scoped, so a guard force-stop releases it

## Still outstanding

None of these are known failures; they are unmeasured.

- [ ] Launch while already in Reverse/Drive cannot survive
- [ ] Background playback is terminated after shifting out of Park
- [ ] File/deep-link launch is terminated while out of Park
- [ ] Head-unit reboot recovers fail-closed (guard restarts via NEMESIS, Plex blocked until Park)
- [ ] Park → Reverse/Drive event-to-stop latency measured from device timestamps
- [ ] No unrelated package/process is killed during the physical shift tests
- [ ] Uninstall via NEMESIS stops the guard, force-stops Plex, and removes `/data/local/safe-plex`

## Safety contract

The supervisor starts blocked and permits playback only when fresh, valid
telemetry proves all of the following:

- `gear.park == 1`
- `moving == 0`
- finite absolute speed within a documented near-zero tolerance
- `driving.restricted == 0`

Missing, malformed, contradictory, stale, or unavailable telemetry is unsafe.
Unsafe state must immediately and repeatedly force-stop `com.plexapp.android`,
including its services and exact child processes.

## Telemetry source

Readings come from the head unit's own factory binders — the same services the
EV6 Plex video gate uses:

- `ISystemService.getGearPStatus()` via `/system/framework/automotive.jar`
- `ITM_HSCANService.getCarSpeed(0)` / `IsCarMoving()` via `/system/framework/com.hkmc.ext.hcan.jar`
- `IRegulationManager.getStatus()` via `/system/framework/automotive.jar`

Unanswered readings are reported as `-` and the service cache is dropped, so the
next poll rebinds from scratch.

## Retired

The HMG-API mod (`geekd4dlabs-safe-plex` 0.1.0) and the guarded test identity
`plex.geekd4dlabs.compat-test` (through 0.1.3) were retired at 1.1.0. The
runtime evidence above applies to the unchanged reviewed APK, guard behavior,
guard scripts, and safety policy carried into 1.2.0. It does not establish
physical validation of the 1.2.0 NEMESIS archive, its metadata, or any vehicle
other than the documented EV6.
