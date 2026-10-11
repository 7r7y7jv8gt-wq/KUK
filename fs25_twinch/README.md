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
