# John Deere 6030 Lights — FS25 compatibility test

The user cancelled the map conversion and authorized FS25 substitutes for missing tractor resources. The working package preserves the tractor geometry, complete light scene graph, light state bindings, added light bar, cruise lights, and double-blink/triple-wait strobes. Original author credits remain in modDesc.xml.

This is a test candidate, not an engine-validated conversion. FS25 and GIANTS Editor cannot run here. No claim is made that it loads, drives, or lights correctly in the game.

Original source: source/FS22_JohnDeere_6030_edit.zip (SHA256 b278ee4d312b991a0b257c7688263dc9534191f15cfc9a32fc13237e6e4652e1). Original source files are unchanged. Output: output/FS25_JohnDeere_6030_Lights_Test.zip; SHA256 f83c10dc8c8a4a3149429b2dbb7ed4fd68b9093da25c3f50ec14e7454d0f0123.

Conversion: modDesc version 92; shop images fixed; legacy vehicle shaders and detail arrays redirected to FS25 fs22support; moved matching textures located; unavailable normal/mask maps use neutral shared assets; missing diffuse atlases use a transparent local texture. Specific-size FS25 tyre meshes replace FS22 generic diameter meshes; missing TM100 sizes use matching-size TM600. Top arms use FS25 XML assets. Diesel tanks receive an exact fill root at the chassis origin. TirePressure uses XMLFile, registered vehicle paths, FS25 Wheel.physics friction and load-finished lifecycle; obsolete suspension deformation is removed.

Checks passed: 44 parsed XML/I3D files; 342 external references found in the supplied FS25 catalog; 505 packaged local references; 44 light node references resolve; identical complete source/output scene graph and geometry; identical light configuration except resource paths; ZIP CRC; isolated Lua 5.1 lifecycle, XML API, configuration activation, bounds, savegame pressure, friction updates and crawler exclusion. These isolated checks stub engine APIs and do not prove runtime compatibility.

Required next validation: put the ZIP in Documents/My Games/FarmingSimulator2025/mods; enable in a test save; buy tractor; exercise shop configurations, drive/steer, hitch implements, refuel, headlights/worklights/turn/brake lights and HOME-key beacons. Return game log.txt and, if materials or collision conversion fail, GIANTS Editor 10 save/log. Collision masks, dashboard emitter shaders, tyre fit, suspension, sound templates, refilling position, attachments, engine behavior and multiplayer remain unverified. InteractiveControl requires a compatible FS25 IC mod.

Tools: tools/convert_tractor.py builds from original input and OVERWRITES its generated output folder and ZIP. Preserve any user-edited output before intentional rebuilds. tools/validate_candidate.py performs the checks above using the retained tools/python-deps Lupa 2.8 Lua 5.1 runtime. No services run. Python3 and Pillow are installed. FS25 asset catalog is retained under /workspace/attachments.
