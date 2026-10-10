# John Deere 6010 lights test v0.3

The edited six-cylinder vehicle previously registered the diode housings as
lights and loaded old FS22 beacon prefabs over flash meshes already in its scene.
This candidate binds the existing emitting surfaces and uses FS25 inline
`beaconLightConfigurations`/`staticLight`/`realLight` definitions, following the
FS25 Fendt example retained in KUK. Static lights use the current `node` field.

- Six white mirror diodes and five white front roof diodes use running lights.
- Seven rear roof diodes have red running cores and brighter brake lenses.
- Twenty lightbar modules, two mirror flash modules and two rear flash modules
  use amber double flash with the beacon/HOME toggle.
- Gentle marker spill works in both graphics profiles. Each flash module has
  its own native beacon light spill. Lamp housings are not emission targets.

The custom shader supplies explicit emission colors, keeps marker lamps steady,
and applies the multi-blink visibility scale to flash meshes regardless of donor
UV/vertex-color authoring. Existing node order, transforms and binary geometry
are preserved. New light nodes are appended after existing children.

## Rebuild

Use the existing isolated checkout; do not create a Git worktree. Python 3's
standard library is sufficient. No services or package installation are needed.
Extract the repository's v0.2 ZIP to a directory outside the checkout, then run:

```sh
python tractor-conversion/jd6010_extra_lights_v03.py \
  --base /workspace/jd6010/output/FS25_JohnDeere6010_Lights_Test_v02 \
  --output /workspace/jd6010/rebuild/FS25_JohnDeere6010_Lights_Test_v03 \
  --report /workspace/jd6010/rebuild/lighting_v03_validation.json
```

Replace `--base` with your extracted directory if different. Output directories
and ZIPs must not already exist; preserve edits before choosing a new output.

## Validation

247 light references resolve, 166 local file references resolve, and 18 packaged
XML/I3D documents parse. Shader variation names resolve to their packaged
definitions. Existing scene node order, IDs and transforms and all six binary
shape files are preserved. The configured waveform has two pulses and a dark
pause per period. ZIP CRC passes. A separate rebuild is compared by SHA256.

FS25/Editor are unavailable in this machine. Shader compilation, native game
asset availability, loading, on/off behavior, brightness, synchronization of
native light spill, performance and multiplayer require an actual FS25 test.
The v0.2 external texture fallback and unused BKT donor variant limitations
remain. Install the ZIP without extracting it, disable older 6010 copies, and
test the six-cylinder in a new test save with both graphics light profiles.
Send a fresh `Documents/My Games/FarmingSimulator2025/log.txt` for failures.
