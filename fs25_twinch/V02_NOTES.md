# T-Winch v02 repair candidate

The supplied FS25 1.24.0.0 log confirmed missing physical wheel shapes, missing vehicle collision flags, missing stock sound node mappings and deprecated folding XML. The original wheel mass of `80` was also incorrect: wheel XML mass is in tonnes, while vehicle component XML mass is in kilograms.

The v02 builder corrects wheel mass to `0.08`, matches wheel contact height to the outer track surface, retains CPU data for collision geometry (`meshUsage=256`), uses modern collision group/filter attributes and the current folding configuration structure. Collision filter values are from the FS25 Fendt reference package already in this repository. Sound references resolve to aliases for the existing rear wheel nodes. The description version is 114, matching the supplied game log.

Both track belts now use 74 links at equal arc-length intervals. Their motion comes from the real displacement of each side of the chassis, so reverse travel reverses the links and turning can move the two belts in opposite directions. Roller, hub and bolt geometry is grouped around rotating pivots. Low-speed pivot behavior uses the documented native Drivable idleTurning setup. Hidden wheel contacts remain a approximation of crawler contact physics.

The single-player recovery winch selects the nearest eligible dynamic vehicle from the same farm within 25 metres. Its cable is rendered as geometry. Pulling uses a tension-only spring/damper, with equal and opposite forces applied at the two component centres of mass. Force is bounded to 25 kN and 3 m/s² per connected component mass. The drum stalls under excessive stretch; connections release outside the allowed range or if the target disappears. No vehicle is teleported. Reeling requires the motor and stops on exit. Connections are not restored from saved games.

This implements recovery of vehicles, not tree/log towing, a ground anchor, a hand-carried hook, a realistic rated 30-tonne winch or multiplayer synchronization. The model and hydraulic linkage still need further detailing and physical validation. The non-binary I3D warning remains expected until resaved through GIANTS Editor.

## Rebuild and check

From this directory, after the original model has been generated:

```sh
python package_mod.py
python package_mod_v02.py
python test_v02.py
```

Python dependencies are Pillow and lupa. The tests exercise Lua with mocked engine calls; they cannot confirm wheel creation, traction, suspension behavior, rendering or gameplay in GIANTS Engine. Fifteen local tests passed for the distributed candidate. In-game validation remains outstanding; follow `TESTING.txt` in the archive using a newly purchased v02 vehicle in a test savegame.

## API references consulted

- [FS25 WheelPhysics API mirror](https://github.com/umbraprior/FS25-Community-LUADOC/blob/main/docs/script/Wheels/WheelPhysics.md): mass units, radius, suspension and contact configuration.
- [FS25 Drivable API mirror](https://github.com/umbraprior/FS25-Community-LUADOC/blob/main/docs/script/Specializations/Drivable.md): native idleTurning.
- [FS25 PowerConsumer API mirror](https://github.com/umbraprior/FS25-Community-LUADOC/blob/main/docs/script/Specializations/PowerConsumer.md): physics forces are in kN.
- [I3D exporter mesh attributes](https://github.com/StjerneIdioten/I3D-Blender-Addon/blob/main/addon/i3dio/ui/mesh.py): CPU mesh retention uses meshUsage 256.
- [I3D exporter object attributes](https://github.com/StjerneIdioten/I3D-Blender-Addon/blob/main/addon/i3dio/ui/object.py): collision filters and compound children.

The official GDN site was inaccessible from this environment; the public API mirror was used for research. No third-party model assets or game assets are redistributed in v02.
