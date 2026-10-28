# Fendt 700 — cruise lights on the normal light switch

[Download the complete updated mod](https://github.com/7r7y7jv8gt-wq/KUK/releases/download/fendt700-cruise-v3-20261028/FS25_Fendt_700_Vario_Gen7_KRISTENSEN_EDIT.zip)

The steady cruise lights now turn on with the normal lights, independently of the beacons. The six orange blitzbar projectors continue to follow the beacon switch.

The cruise mesh `0>0|5|2|1|5|4` has one normal `defaultLight` registration with `lightTypes="0"` and intensity 80. Its beacon static-light registration was removed, so the two controllers cannot override each other.

This version preserves the 13 red rear diodes, eight white mirror diodes, six switched blitzbar projectors and the BKT tire/rim fit fix. Only `vario700.xml` changes from the previous lighting release; all other 98 files are byte-identical.

Replace the existing mod ZIP, keep its filename, and restart FS25.

Control checks used the actual official `StaticLight` and `BeaconLight` Lua method bodies with stubbed engine APIs:

| Normal lights | Beacons | Cruise intensity | Orange projectors |
| --- | --- | --- | --- |
| Off | Off | 0 | Hidden |
| Off | On | 0 | Visible |
| On | Off | 80 | Hidden |
| On | On | 80 | Visible |

Additional toggles preserved independent controls, bank flash phases and the Real Beacon Lights setting. XML, all custom light paths, source-file comparisons, CRCs and SHA-256 passed. This is a control-logic check; live FS25 rendering was unavailable.

ZIP SHA-256: `2a746d9c2335587dd1672e82c5296b096d00d21a7dbe710a11c3d756015569c4`

The binary parts are release assembly inputs; download the complete release ZIP for installation.
