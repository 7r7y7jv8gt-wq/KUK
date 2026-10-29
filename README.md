# Tume HKL3000 — detailed, weathered 3D model

A reference-led revision of the earlier model. The source photographs are from [Klaravik auction 1088608](https://www.klaravik.se/auktion/produkt/1088608-samaskin-tume-hkl3000/). The 3 m working width comes from the listing; the other dimensions, row count, tire count and wear are visual approximations, not measured manufacturing data or a scan.

## Open the model

- **Blender:** open `Tume_HKL3000_real.blend`. Keep the `textures` folder beside the file. This contains the full PBR material setup.
- **Blender studio:** `Tume_HKL3000_studio.blend` includes cameras, lighting and a concrete preview floor; press F12 to render. The floor/lights are staging props, not part of the seeder.
- **glTF:** open `Tume_HKL3000_real.gltf`. Keep its `.bin` and `textures` folder in place. This also carries albedo, normal, roughness and metallic textures.
- **FBX:** import `Tume_HKL3000_real.fbx` with the adjacent textures. Material interpretation varies between applications; Blender/glTF retain the most complete material setup.
- **GIANTS Editor:** first extract `Tume_HKL3000_I3D_geometry.zip` into this same folder. Then import `Tume_HKL3000_real.i3d`. The I3D uses local albedo/normal maps and simplified specular settings; it does not preserve the complete Blender PBR shader.

## Changes from the first version

- Shallow automotive road-tire tread, rounded sidewalls and dished rims with actual ventilation holes.
- Closed articulated chain loops and sprockets, shafts, retaining clips and the triangular side guard.
- Adjustable round top-link, slack hydraulic hoses, connector crimps and front metering mechanism.
- Scalloped rear guard, rusty fastening hardware and pointed fertilizer shoes.
- Subtle sheet deformation and smaller folded-edge bevels.
- Eight 1024-pixel PBR material sets with worn red paint, patchy corrosion, scuffs, dusty rubber and aged marking colors.

Model coordinates: Blender Z-up, FBX/glTF/I3D Y-up, dimensions in metres. Wheel objects have separate pivots and share mesh data.

This is a static visual model, not a working FS25 sowing machine. It has no gameplay XML, collision, filling, seeding or animations. It is not a ready-to-install mods-folder ZIP.

I3D schema, normals, geometry indices, texture paths and archive integrity were checked. The model was rendered for visual inspection; GIANTS Editor and FS25 were not run. Auction photos are not included or reused as distributed image textures.
