# Scania S Tridem — lighting update

[Download FS25_ScaniaS_Tridem.zip](../FS25_ScaniaS_Tridem.zip?raw=true) · [Lighting code reference](LightingCode.xml)

Replace the original ZIP in your mods folder and keep its filename unchanged. Do not unpack the installed mod. Restart FS25 after replacing it.

| Briod state | White DRL intensity | Main-lamp intensity |
|---|---:|---:|
| Engine off, lights off | 0 | 0 |
| Engine running, normal lights | 80 | 0 |
| Engine running, full-light stage | 80 | 800 |

The seven Briod DRLs now use native daytime-light control: engine start enables them, engine stop disables them, and selecting full lights keeps their intensity at 80. The seven main lamps use the truck's existing full-light stage (`lightTypes="2"`) at 800.

The Optibeam/blitzbar has its own cruise-light entry and mapping at intensity 8, matching its existing setup. It uses its original amber material 1202, original additive_colorScale glow shader, colorScale 1 0.5 0, and lightControl parameter. Its cruise lights stay steady with the engine and are separate from the bar's strobe meshes. The reference XML is for reading/copying; it is already installed in the vehicle XML.

All earlier repairs remain: stock lamps behind the Briods removed, texture paths corrected, all 66 side diodes orange, and stale light/beacon references corrected.

Checked XML, node mappings, controllers, material preservation, and archive CRC. Live appearance/gameplay still needs testing in FS25 or GIANTS Editor.

Implementation references: [GIANTS Lights](https://gdn.giants-software.com/documentation_scripting_fs25.php?version=script&category=78&class=691), [GIANTS StaticLight](https://gdn.giants-software.com/documentation_scripting_fs25.php?version=engine&category=14&class=168), [FS25 glowShader source copy](https://github.com/hipsterjazzbo/fs25_animals_tmp/blob/main/FS25_AnimalPackage/placeables/productionPoints/eggIncubator/glowShader.xml).
