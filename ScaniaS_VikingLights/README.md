# Scania S — three-way Viking markers

Complete mod: [`FS25_ScaniaS.zip`](../FS25_ScaniaS.zip), version **1.0.2.2**, built from the owner's new three-part RAR.

All six fitted GeoViking lamps on the S 6x4 now show white forward, amber outward and red rearward, intensity 20. Both LODs use native `defaultLight lightTypes="0"`, following the truck's regular lights exactly like the Semi Lowloader 3A setup.

The Scania light assembly has a 180-degree parent rotation. The source mesh named `rearGuides` actually points toward the vehicle front, so it receives the white material; `frontGuides` receives red. Existing fixture positions are unchanged. New 24 mm amber side guides reuse the owner's ring geometry against the outer rubber housing, matching the validated trailer geometry.

The imported Viking emission and dirt maps referenced absent OneDrive files. White, red and amber emission maps are now bundled; missing dirt maps use the neutral native vehicle mask. Original dirt detail may differ. Every local I3D resource resolves.

The original shape binaries, other assets, 4x2/8x4 variants, other lighting controls, four name choices and original flag textures, curtains, grille-sign IC and vehicle settings are preserved from this upload. Briod high beams remain 200 and their white DRLs remain 40.

Exit FS25 fully, replace `FS25_ScaniaS.zip`, keep the filename, and restart. XML, all 36 new controls, 640 mappings, 1,099 vehicle references, source-file identity, physical light directions and ZIP CRC passed validation. [Geometry preview](VikingPreview.jpg) uses decoded source meshes and the actual candidate hierarchy with simulated emission in Blender. **No live FS25 game test has been performed.**
