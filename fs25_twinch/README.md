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
