# Bergaas Scania Tipper Pack — lights and window names

[Download the complete mod](../FS25_BergaasDesign_Scania_Tipper_Pack.zip), version **1.0.0.3**. Both original tipper trailers are included.

## Visible Optibeam double flashes

The Optibeam flash mesh now uses a **bar-only copy of the native FS25 vehicle shader**. Exactly one expression changes: every flash surface explicitly selects the shader's existing **multiblink** branch. This prevents the main LED panels from remaining steadily lit because of the native channel type mask.

The native multiblink formula, alternating phase parameters, lightIds on/off activation, emission atlas, all geometry/UVs and native projected-beacon controls remain unchanged. The two outer engine-on cruise sections retain their own steady control. No runtime Lua script or input binding is added. [Exact shader code](OptibeamBlinkShader.xml).

The earlier native-controller audit assumed mask10 without establishing its value from the running game. Loading and projected-light pulses passed that check while visible emission still remained steady. This release removes that mask dependency for the bar's flash surfaces; the new shader audit supersedes the earlier visible-blink claim.

## Retained setup

- **Seven roof markers:** the center marker uses the same position-light circuit and intensity **30** as the other six.
- **10 OZZ/Briod lamps:** white engine-on DRL **20**, high-beam glow **50**, projected range **100 m**, reduced projected brightness and a wide fan.
- **Optibeam:** alternating double flashes **12**, six projected beacons at **100 m**, separate steady orange engine cruise lights **8** at the outer ends.
- **Vindu navn:** **J. Kristensen** (default) or **M. Kolbræk**, fitted to the driver-side window. Original lettering, Norwegian flags, alpha and mipmaps are unchanged. [Placement preview](WindowNamesPreview.jpg) is a geometry preview.

All original main models, shape binaries, textures, name configs, truck controls, both trailers and integrations remain unchanged from version1.0.0.2. The update changes only the external flash model's shader file reference, mod version and README, and adds the local shader. The corrected component-based beacon wrapper indices remain intact.

## Installation and validation

Exit FS25 fully, replace **FS25_BergaasDesign_Scania_Tipper_Pack.zip**, keep the filename, and restart. Use the vehicle's normal beacon switch to activate double flashing. Cruise lights follow the engine independently.

The final ZIP contains **82 files**. Its CRC and every archived file are checked against the validated candidate. All **51 local I3D resources** resolve, including the new relative shader path; the **719 vehicle node references** remain unchanged from the checked previous release. Independent comparison proves all other **78 existing files** are byte-identical.

The isolated native pulse expression was compiled and executed using Mesa OpenGL4.5/EGL with llvmpipe, across **10,001 time samples**, both used UV channels, masks0/8/10 and inactive IDs. Both sides produce two alternating pulses per cycle, reach exact zero between pulses and remain dark when switched off. This executes the isolated expression; it is **not a full GIANTS shader compilation or live FS25 rendering test**.

See [release validation](validation.json), [bar audit](BarValidation.json), [shader source audit](ShaderEmissionValidation.json), [isolated shader execution](IsolatedShaderExecution.json), and [independent regression](FollowupRegression.json). The retained OZZ/name reports cover unchanged assets. **No live FS25 game or GUI test has been performed.**
