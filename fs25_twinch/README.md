# T-Winch reference model

Approximate static model created from the supplied images, using estimated dimensions rather than engineering drawings. Contains 525 meshes and 15,264 triangles. No third-party model assets are included.

## Files

- `twinch.i3d`: GIANTS XML scene with embedded triangle geometry and simple materials. Uses metres, Y up. Does not require an external `.i3d.shapes` file.
- `twinch.blend`: editable Blender 4.3 source, Z up.
- `twinch.obj` and `twinch.mtl`: interchange fallback, Y up.
- `preview.png`: rendered reference preview.
- `build_model.py`: procedural generator. Run `blender -b --python build_model.py` from this directory to regenerate the files.

## FS25 handoff

Open `twinch.i3d` in GIANTS Editor 10 compatible with your FS25 version. Inspect import warnings, dimensions, materials and orientation, and save through the editor to its native format. The XML structure, triangle indices and material/shape references have been checked here; GIANTS Editor and FS25 were unavailable, so actual compatibility has not been verified. If the XML geometry importer rejects the scene, use the Blender source with the official compatible GIANTS exporter.

This is a static model asset, not an installable vehicle mod. Vehicle XML, modDesc.xml, collision/rigid-body setup, component mappings, track animation, hydraulic/blade animation, winch functionality, lights, sounds, store assets and in-game validation remain to be implemented. Meshes are named for editing but currently placed directly under one root; movable assemblies will need grouping and suitable pivots before animation. Materials use plain colors; no production UV atlas or FS25 vehicle shader is provided. Dimensions and markings are approximations.

## Version 04 installable mod

Download `FS25_TWinch_v04.zip` at repository root. Disable older T-Winch versions and purchase a new v04 vehicle in a test save. Start the motor, hold left mouse button and drag vertically to operate the blade. Ctrl+B attaches/releases the recovery winch to a nearby same-farm vehicle; Ctrl+R reels and Ctrl+N pays out. Winch implementation is single-player vehicle recovery, not timber winching.

V04 adds a bent tapered blade, cutting-edge bolts, reinforcement towers, reflector strips, open fairlead and rollers, interlocking recovery chain, front grille and cable drum. Original 1024px diffuse, normal and gloss DDS texture sets have complete mip chains. Geometry and proportions are approximations based on the supplied photographs. It uses generic I3D materials; FS25-specific dirt/wear shader integration is not implemented.

Rebuild with `python fs25_twinch/package_mod_v04.py`, render with `blender -b -t 8 --python fs25_twinch/render_v04.py`, and check with `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v04.py` (Pillow, NumPy and lupa required). `preview_v04.png` is a Blender render, not an in-game screenshot. FS25 and GIANTS Editor validation remain pending.

## Version 05

`FS25_TWinch_v05.zip` removes the protruding green fairlead, rollers, hook and hanging cosmetic chain shown in the user's screenshot. The working cable outlet is recessed into the front plate. Two exposed green hydraulic cylinders, chrome pistons, clevis brackets, pins, fittings and supply hoses follow the native blade movement. Start the motor; hold left mouse and drag vertically to raise/lower the blade.

Both tracks retain their independent movement controls, with 74 linked steel shoes per side. Each shoe now includes a shaped plate, grouser, rail, hinge pin, guide horns and bolt heads. Rear sprockets have teeth; undercarriage guards and wheel rims add structure. Texture maps use restrained paint variation and darker steel with local wear and grime. Normal-mapped meshes request GIANTS tangent generation; collapsed legacy text triangles and zero normals are repaired.

Build: `python fs25_twinch/package_mod_v05.py`. Render: `blender -b -t 8 --python fs25_twinch/render_v05.py`; add `-- --raised` for the raised-blade preview. Rebuild after rendering to refresh store icons. Check: `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v05.py` with Pillow, NumPy and lupa installed. Blender previews show geometry/materials, not live GIANTS physics. Native FS25/Editor testing remains pending, and track ground contacts remain an approximation.

## Version 06: input and native material correction

The supplied v05 game log confirms a duplicate `cylindered` specialization inherited from `baseDrivable` and missing FULL-axis direction labels. V06 removes the duplicate declaration and supplies both labels. V05's checks did not exercise the live control path, and the user reported that both blade and cylinders remained stationary. V06 removes the native Cylindered controller and explicitly registers the hydraulic blade action in TWinch. Custom actions are registered by name instead of relying on built-in `InputAction` enum entries; all blade and winch help entries are made visible. A fresh `TWINCH_BLADE_LIFT` action avoids inheriting old custom bindings. Registration supports active-vehicle input even when selection points elsewhere. With the engine running, left mouse plus vertical movement controls the blade; Page Up raises and Page Down lowers. The single-player server tick moves the blade, aligns both barrels/rods with their endpoints, stops after input ends, clamps travel, and saves the angle. Existing track and recovery-winch logic is retained.

Materials now use `$data/shaders/vehicleShader.xml`, the stock default vehicle mask and FS25's built-in paint, cast iron, scratched metal and rubber detail-library resources. Original surface textures add scratches and concentrated blade/track grime. The generic RGB gloss maps are retained only for the Blender preview; they are not used as the native vehicle shader's vehicle mask. Blender previews cannot reproduce the built-in GIANTS shader finishes because game resources are unavailable here.

Build with `python fs25_twinch/package_mod_v06.py`, render with `blender -b -t 8 --python fs25_twinch/render_v06.py`, rebuild to refresh store images, then run `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v06.py`. Tests now load the packaged Lua and exercise registered action → input callback → server update → blade rotation and cylinder alignment, plus limits, stopping and persistence. Actual FS25/Editor validation remains pending. Disable older versions and purchase a new v06 machine.

## Version 07: deeper blade travel

`FS25_TWinch_v07.zip` extends the blade's lowered angle from 0 to +25 degrees while retaining -28 degrees raised. The cutting edge can reach about 34cm farther down relative to the chassis. Chrome rods are extended from .55m to .65m, keeping more than .10m overlap throughout the range. The old rectangular collision is replaced by a closed shell matching the bent plate and cutting edge. Ground contact may limit downward movement or support/lift the front of the machine; this is not terrain deformation.

Build with `python fs25_twinch/package_mod_v07.py`, then run `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v07.py`. The 32 local checks include full-range hydraulic overlap, the new lower limit, and restoring the lowered position. Native engine contact and stability still require FS25 testing. Start the engine and use Page Down or left mouse vertical control to lower the blade. Disable older versions and purchase a new v07 in a test save.

## Version 08: on-foot blade winch and TerraFarm

Download `FS25_TWinch_v08.zip` at repository root, disable earlier T-Winch versions and buy a fresh v08 in a test save. Walk within 2.5m of the blade and press R to take the hook. Aim at a tree/log/movable object within 4m and press R again to attach. Hold Z to reel, Shift+Z for faster reeling, X to pay out; Shift+R disconnects all and returns the hook. Reeling requires a running engine; disable automatic engine stop if the game turns it off when you leave the machine. Remote controls work within 60m. The old Ctrl+B vehicle recovery mode is exclusive with this new logging mode.

Static trees provide a fixed recovery anchor; dynamic objects are pulled with equal chassis reaction. Up to eight objects / eight tonnes can be attached, with additional logs within 15m of the first. Take an additional chain with R at the blade. Forces are unilateral, damped and bounded; this is original single-player force simulation, not the Tajfun PTO or implement-joint specialization. Connections are temporary and are not persisted across saves. Deleted objects and overrange connections release safely. A global mod listener updates the player input context while the vehicle is parked, so entering/selecting the machine is not required for the prompt.

The uploaded 50keda Tajfun mod supplies only its private hook/chain material holder, chain shader, textures and sounds, with attribution in CREDITS.txt. The Tajfun body and full vehicle/scripts are excluded. Earlier removal of the green fairlead and hanging decorative recovery chain is preserved. The new small hook sits at the blade outlet and follows the carried/attached endpoint; a second hook supports taking an additional chain. Cable segments show slack, respect terrain height and follow the hydraulic blade anchor.

Install [FS25 TerraFarm](https://github.com/scfmod/FS25_TerraFarm/releases) separately. Keep the vehicle ZIP named `FS25_TWinch_v08.zip`; TerraFarm's documented `machineConfigurations.xml` discovery adds its specialization only when installed. The native Leveler specialization uses a separate material fill unit (index 2) without changing diesel (index 1). The work reference is parented to the moving blade's actual cutting edge, width 2.23m. Enable the machine in TerraFarm, choose FLATTEN, SMOOTH, LOWER or PAINT, and lower the blade. Blade collision is disabled by TerraFarm while the machine is active, following its documented collision handling. TerraFarm governs land access, costs and terrain settings.

Rebuild with `python fs25_twinch/package_mod_v08.py` after extracting the user-supplied Tajfun ZIP to `/tmp/tajfun-inspect`; run `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v08.py` (Pillow and lupa). An optional upstream TerraFarm checkout in `/tmp/twinch-terrafarm` enables the test running its actual MachineWorkArea implementation; the reference revision is recorded in validation.json. All 43 local checks passed, covering baseline physics/tracks/blade controls, registered player events through attachment and server forces, fixed and dynamic targets, cleanup, limits, asset references and TerraFarm work area contact. No FS25 or GIANTS Editor engine test has been run.

### v08 shop-loading hotfix (0.8.0.1)

The supplied in-game log showed `Not all prerequisites of specialization 'leveler' ... are fulfilled`, followed by `Unknown type 'twinchV08'` each time the shop item was opened. Leveler requires both FillUnit and BunkerSiloInteractor; the original v08 declared only Leveler and relied on the inherited FillUnit. The hotfix adds BunkerSiloInteractor before Leveler, preserving the inherited FillUnit without a duplicate declaration. The regression suite now checks the native prerequisite predicate, including both missing-dependency cases; all 44 local tests pass. Actual shop preview and purchase still require an FS25 run.

The download retains the name `FS25_TWinch_v08.zip` so TerraFarm discovery and the existing vehicle type remain consistent. Close FS25, remove the older ZIP and any extracted `FS25_TWinch_v08` folder from the mods directory, then install the replacement ZIP without unpacking it and restart the game.

## Version 09: excavator undercarriage and underside drive

`FS25_TWinch_v09.zip` reduces both operating winch hooks to one tenth of the previous size (uniform scale .14 → .014). The uploaded excavator photograph guides the undercarriage: narrower 400mm single-grouser steel shoes, articulated chain rails/pins, recessed twin-shoulder end wheels, paired road wheels, toothed rear sprockets, upper return rollers, carrier box sections and a sliding idler/grease tensioner. The 74-link independent animation loops are preserved. The track centers and wheel physics move together from ±.88m to ±1.10m; track inner edges at ±.90m provide at least 55mm clearance from the central chassis and hydraulic mounting ears.

Underneath, visible hydrostatic drive components include a central gearbox/sump, crossmembers, protected belly plate, travel motors, final-drive reduction housings, output shafts and hydraulic supply lines. These are model components; the existing hydrostatic motor/wheel driving physics remain in use. The blade motion, on-foot winch, TerraFarm configuration and shop prerequisite hotfix are retained. Disable older versions and install the v09 ZIP without unpacking it; TerraFarm discovery uses that filename.

Build with `python fs25_twinch/package_mod_v09.py`, render with `blender -b -t 8 --python fs25_twinch/render_v09.py`, build once more to refresh store thumbnails, then run `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v09.py`. The preview is a Blender render with approximate materials, not an FS25 screenshot. All 45 local checks cover mesh references, crawler/frame clearance, track/wheel animation, hook scale, underside components and the retained blade/winch/TerraFarm behavior. Actual FS25 validation is pending.
