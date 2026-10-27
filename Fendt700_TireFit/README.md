# Fendt 700 Vario — custom BKT tire/rim fit

[Download the complete edited mod ZIP](https://github.com/7r7y7jv8gt-wq/KUK/releases/download/fendt700-tire-rim-fit-20261027/FS25_Fendt_700_Vario_Gen7_KRISTENSEN_EDIT.zip)

The custom white-letter BKT tires were enlarged on an ancestor transform that FS25 discards when loading the selected tire node. The rims and wheel physics already included that enlargement, so the tires loaded smaller than intended.

The uniform scale now lives on the selected `0|0` LOD group. Front tires retain the intended 5% enlargement and rear tires 15%. Their complete hierarchy dimensions in GIANTS Editor are preserved.

| Tire file | Loaded LOD scale |
| --- | --- |
| `BKTHVIT/600_60R28.i3d` | `1.1749815 1.05 1.05` |
| `BKTHVIT/710_60R38.i3d` | `1.28685 1.15 1.15` |

Only these two I3Ds changed. All 97 other files are byte-identical to the supplied mod. Geometry, lettering, textures, child LOD adjustments, wheel configurations, rim dimensions, offsets and physics remain as supplied.

Replace the existing mod ZIP with the download, preserve its filename and restart FS25. The change applies to the **BKT med hvit skrift (600/60R28 + 710/60R38)** wheel option.

Validation covered XML parsing, selected-node scales, preservation of complete asset transforms, asset references, archive membership, CRCs and SHA-256. Live testing in FS25/GIANTS Editor was unavailable.

[FS25 wheel loading reference](https://gdn.giants-software.com/documentation_scripting_fs25.php?version=script&category=93&class=912), `onPartI3DLoaded` and `setNode`.

ZIP SHA-256: `4c0e59321c8334e698d36464bbab193f120f1b1f0f4b157407d1d0269556b9ec`

The binary parts in this folder are release assembly inputs; download the complete release ZIP for installation.
