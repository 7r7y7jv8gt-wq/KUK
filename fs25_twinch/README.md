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

## Version 10: protected hook size and uploaded Engelsen TerraFarm pack

`FS25_TWinch_v10.zip` separates each hook's .014 mesh scale from a parent pose transform. World position/direction updates operate on the parent, with normalized direction and a vertical-direction fallback; docking and cloning explicitly preserve child scale. This addresses the oversized hook reported in-game after v09. Tests deliberately simulate a direction update resetting the pose scale and verify that the carried, attached, extra-chain and docked mesh sizes stay .014. Actual FS25 visual verification remains pending.

The companion `FS25_0_TerraFarmMachines_Engelsen_Anlegg.zip` adds `FS25_TWinch_v10/twinch.xml` to the uploaded pack's registry. Its original registry had a premature closing tag followed by additional Engelsen configurations and another closing tag; this was invalid XML. The repaired registry retains those entries within a single root. The uploaded dozer leveler profile is adapted to the moving `terraFarmBladeEdge` reference with a 2.23m width; original dozer offsets are not copied because their reference origin differs. FLATTEN, SMOOTH and PAINT are retained, along with the T-Winch's LOWER mode. All original machine XML files and other pack assets remain in the companion archive; only registry, addon version and the new T-Winch profile are changed/added, plus an attribution note.

Replace older T-Winch and Engelsen packages with both downloads without unpacking them. FS25_0_TerraFarm itself must be installed separately. Enable the T-Winch machine in TerraFarm, choose the terrain mode and lower the blade. The same blade profile is included internally for standalone compatibility; both registry entries resolve to equivalent configuration. The existing crawler/drivetrain, blade controls, on-foot logging winch and Leveler prerequisite fix are retained.

Rebuild using `python fs25_twinch/package_mod_v10.py /path/to/original/FS25_0_TerraFarmMachines_Engelsen_Anlegg.zip`, then `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v10.py`. All 47 local tests passed, including the protected hook hierarchy, full addon XML parsing and T-Winch/Engelsen registry entries. FS25 is unavailable here, so in-game testing is still required.

## Version 11: supplied Volvo crawler mesh

`FS25_TWinch_v11.zip` installs the uploaded `ec380DLCrawler.i3d`, its unchanged compiled `.i3d.shapes` geometry and adapted crawler XML. This is the supplied Volvo asset, including two detail levels per side and mud meshes, replacing the visible procedural track shoes. Files reference only built-in FS25 shaders, detail-library textures and the Volvo crawler motion-path array. No extra texture upload is required by this I3D; actual stock-resource availability needs engine verification.

Native Crawlers animates each side from its powered wheels (left indices 1/3; right 2/4). Before vehicle type validation, native Crawlers is added only if missing, avoiding duplicate inherited specialization failures. The existing procedural link nodes are hidden, while T-Winch running-wheel animation remains active. A 74-node clamp prevents an asynchronously appended Volvo track from being moved as an old procedural shoe. The axle, gearbox/final drives, blade, hook pose fix and on-foot winch controls remain.

Initial fitting scale is .65 across, .8 vertically and .65 longitudinally; original .96 scale is adjusted and scrolling rate compensates for longitudinal scaling. These are estimated fitting values. The compiled geometry could not be inspected/rendered in this workspace, so its exact dimensions, origin, orientation, frame clearance and ground fit remain unverified until FS25/Editor testing. Older screenshots/store thumbnails illustrate the underlying T-Winch; they do not preview the imported Volvo mesh. If the imported tracks need adjustment, edit the two scene-root scale values in `crawlers/volvo/ec380DLCrawler.i3d` and retest in engine.

Disable older T-Winch versions and install the unopened v11 ZIP, then buy a fresh v11 in a test save. The embedded TerraFarm registry now points to v11, so the existing Engelsen addon may stay installed without another addon update. Build with `python fs25_twinch/package_mod_v11.py` while the uploaded crawler files are present at the paths defined in that script. Run `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v11.py`. All 49 local checks passed, including byte-identical supplied geometry, external asset/config references, stock resources, per-side wheel mappings, hidden old shoes, guarded native specialization registration and retained blade/winch/TerraFarm logic. This does not validate native shader rendering or imported geometry fit.

## Version 12: walk-up winch, blade controls and 40-tonne mass

`FS25_TWinch_v12.zip` uses player-root proximity within 3m of the blade for the R prompt, refreshes registration after player input contexts rebuild, retries failed event registration atomically and uses fresh versioned action names. Carried hook drawing still uses the hand node. Reel and blade inputs can start the engine. Both hydraulic assemblies are explicitly visible; left mouse plus vertical drag or Page Up/Page Down controls the blade after engine startup.

The chassis component is 39,680kg plus four 80kg support wheels, giving a configured total of 40,000kg. Suspension load, spring and damping are scaled to the added chassis mass. Handling and ground stability require FS25 testing. Disable older T-Winch packages, install the unopened v12 ZIP and purchase a fresh vehicle in a test save.

The supplied Volvo crawler files contain shoes and mud meshes only. Their geometry is retained; transferring the actual Volvo frame, wheels and final drives still requires its main I3D and matching shapes. Local tests do not verify FS25 rendering, geometry fit or in-game interaction. Build with `python fs25_twinch/package_mod_v12.py`; run `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v12.py`.

## Version 13: blade input recovery and darker undercarriage

The supplied log loads both v10 and v12. Repeated v10 `draw` errors come from the winch drawing helper sharing a name with a mod-listener callback: FS25 calls it with the listener instead of a winch instance. V13 renames the helper to `drawWinch` and covers the listener contract in a regression test. Disable all earlier T-Winch versions; this build cannot patch an independently loaded v10.

V13 uses fresh mouse-axis bindings and separate Page Up/Page Down raise/lower events with press, release and continuous callbacks. It explicitly activates the blade event and retries registration while the vehicle is active for input. Blade movement also runs through the frame update, independent of physics-tick availability; a mission-time guard prevents applying it twice per frame. Barrel and rod endpoint alignment remains part of every blade movement.

The Volvo crawler motion-path geometry is retained with darker shader/base steel tint. Exposed carrier plates, wheel axles and hubs use a dedicated dark steel material. A deterministic, restrained cast-steel diffuse texture replaces the mottled brown wheel finish. The full Volvo drivetrain remains unavailable in the supplied crawler-only assets. These changes need in-game visual inspection; shop images have not been regenerated to represent the imported geometry.

Mass remains 39,680kg chassis plus four 80kg support wheels. Build using `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/package_mod_v13.py`; validate using `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v13.py`. All 56 local checks pass. FS25 is unavailable here, so this is not proof of functioning controls, terrain handling or materials in the game. Install the unopened v13 ZIP, with earlier versions disabled, and buy a fresh vehicle in a test save.

## Version 14: user-installed Lizard FOR9T lights

The uploaded ZIP contains edited I3D/compiled shapes and FOR9T prefab assets, rather than a complete vehicle mod. V14 combines them with the v13 vehicle package, preserving the eight user placements and byte-identical compiled shapes. Existing I3D mappings are rebuilt after Editor node reordering; unused mappings for removed roof/exhaust geometry are discarded.

Eight native `dayTimeLight` entries activate the red DRL shader meshes with the engine. White/orange DRL alternatives are hidden. Eight native static work lenses and eight real spotlight beams use front/rear light types 0/1, with both low/high graphics profiles supported. F cycles front work lights, then front and rear lights. The old four beam nodes are retained for stable scene indices but disabled and removed from the lighting configuration. The supplied FOR9T prefab is by 5oteruud; its assets and author metadata remain included.

V13 blade/winch logic and 40-tonne configuration remain. Five package checks pass, covering asset references, mappings, geometry preservation, lighting entries and ZIP installation structure. No FS25 visual/runtime test was possible; brightness, aim and emissive appearance require in-game verification. Disable earlier versions and install the unopened v14 ZIP. Rebuild with `python fs25_twinch/package_mod_v14.py`, then `python fs25_twinch/test_v14.py`. Source model/prefab inputs are saved in `fs25_twinch/user_for9t`.

## Version 15: rear logging winch and lit FOR9T centers

Duplicates the existing drum/cable geometry into a close-mounted rear assembly with a lower bumper-based backing plate. Its fairlead is at (0,1.2,-1.49). Both front and rear fairleads register independent logging states and use the same nearby R interaction, pull/payout controls, force limits, hook sizing and cleanup. Nearest-fairlead selection chooses the operating winch; each retains its own rope and targets. Legacy vehicle-recovery controls remain at the front anchor.

The reported in-game first-lit bank was the rear. V15 reverses bank assignments: negative-Z lamps use the first lighting stage, positive-Z lamps join in the second. Eight emitting work-light insert meshes, switched by native StaticLight visibility, illuminate the reflector centers independently of the prefab's UV light slots. Red engine-controlled DRLs remain. User lamp placements and compiled geometry are unchanged.

Twenty-two local checks pass, including front winch regressions, rear nearest-hook selection and cleanup of both states, light bank pairing, glowing insert configuration, asset/mapping checks and ZIP integrity. No FS25 rendering/operation test is available; rear plate fit and lamp glare need in-game inspection. Build with `python fs25_twinch/package_mod_v15.py`, validate with `PYTHONPATH=/tmp/twinch-test-deps python fs25_twinch/test_v15.py`. Disable earlier versions and purchase a fresh v15 for testing.
