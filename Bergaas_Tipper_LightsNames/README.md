# Bergaas Scania Tipper Pack — lights and window names

[Download the complete mod](../FS25_BergaasDesign_Scania_Tipper_Pack.zip), version **1.0.0.2**. Both original tipper trailers are included.

## Version 1.0.0.2 fixes

The center roof marker was missing its native position-light controller. All seven now use the same circuit and intensity **30**, with their original models and placement.

The Optibeam flash controllers previously failed to register: BeaconLight resolves node indices relative to an I3D components array, while the generated wrappers used Scene-relative paths. Both wrappers now select the component with **`rootNode="0>"`** and its flashing Shape with **`staticLight node="0>0"`**. The generated mesh also declares tangent generation, matching the source mesh's tangent stream. No flash geometry, UV mapping, material or placement is changed.

The earlier loading audit contained an incorrect mock for paths without a component selector. The corrected audit reproduces the previous failure and passes the repaired wrappers using the native GIANTS resolver. The published resolver body is from FS22; its component contract is also demonstrated by the supplied FS25 beacon assets and FS25 BeaconLight implementation. This is a loading and timing check, not an FS25 rendering test.

## Lighting and names retained

- **10 OZZ/Briod lamps:** white engine-on DRL **20**, high-beam glow **50**, projected range **100 m**, reduced projected brightness and a wide fan.
- **Optibeam:** alternating native double flashes **12**, six projected beacons at **100 m**, separate orange engine cruise lights **8**.
- **Vindu navn:** **J. Kristensen** (default) or **M. Kolbræk**, fitted to the driver-side window. Original lettering, Norwegian flags, alpha and mipmaps remain unchanged. [Placement preview](WindowNamesPreview.jpg) is a geometry preview.

All original main models, shape binaries, textures, names, truck settings, both trailers and integrations remain unchanged from the previous release. The update changes only six files: the missing roof-marker controller, two beacon wrapper paths, the generated flash mesh's tangent declaration, mod version and README.

## Installation and checks

Exit FS25, replace **FS25_BergaasDesign_Scania_Tipper_Pack.zip** with the full ZIP, keep the filename, and restart. Activate flashing with the vehicle's normal beacon switch; cruise lights follow the engine independently.

The final package has **81 files**, **719 checked vehicle node references**, **50 resolved local model resources**, seven controlled roof markers and an intact ZIP CRC. Corrected native loading checks register all six bar controllers, retain two external meshes and six projected lights, and verify two pulses per cycle on each side. Independent checks preserve all unrelated XML and asset bytes. See [validation](validation.json), [bar loading audit](BarValidation.json), [before/after regression](BeaconNodePathRegression.json), and [independent regression](FollowupRegression.json).

The OZZ, name and shader-interface reports describe unchanged work from version 1.0.0.1. Current asset, bar and native-beacon reports supersede the earlier loading audit. **No live FS25 game, GUI or GPU shader-compilation test was performed.**
