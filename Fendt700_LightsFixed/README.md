# Fendt 700 — rear, mirror and blitzbar lighting fixes

[Download the complete updated mod ZIP](https://github.com/7r7y7jv8gt-wq/KUK/releases/download/fendt700-lights-v2-20261027/FS25_Fendt_700_Vario_Gen7_KRISTENSEN_EDIT.zip)

- All 13 small rear cab diodes glow **red** with the normal position lights.
- Four small diodes on each mirror glow **white** with the position lights.
- All six orange blitzbar projectors follow the beacon switch and preserve the existing alternating bank phases.
- The bar's orange cruise strip stays steady while beacons are on and goes dark when they are off.
- Includes the previous white-letter BKT tire/rim fit fix.

The diode controls referenced hidden or nonexistent lens nodes. They now target the existing visible red and white lenses, at the original intensity 80. Two obsolete OZZ entries were removed; the remaining OZZ/FOR9T controls and normal vehicle lights are preserved.

Only two of the blitzbar's six projectors had beacon controllers. All six are now registered using the native FS25 embedded beacon syntax and start hidden. The cruise mesh is controlled only by the beacon system, avoiding competing running-light writes.

Compared with the tire-fixed version, only `vario700.xml` and six projector startup visibility flags in `vario700.i3d` change. All 97 other files are byte-identical. Meshes, textures, materials, node paths, IDs, beam transforms and the tire fix remain intact.

Replace the existing ZIP with the download, keep its filename, and restart FS25. Use the normal lighting and beacon controls.

Validation includes all custom light paths, matching visible lens materials, six beacon controllers, initial visibility, XML parsing, source-file comparisons, ZIP integrity and SHA-256. Actual official `BeaconLight` Lua method bodies also passed on/off, return-to-off, same-bank timing and Real Beacon Lights option checks with stubbed engine APIs. Live GIANTS rendering and shader compilation were unavailable.

[Official FS25 BeaconLight reference](https://gdn.giants-software.com/documentation_scripting_fs25.php?version=script&category=14&class=165)

ZIP SHA-256: `b21e78b5d1e9e97cd35004134c084d9ea503b1679ac08ea19deff06e8b542b15`

The binary parts in this folder are release assembly inputs. Download the full release ZIP for installation.
