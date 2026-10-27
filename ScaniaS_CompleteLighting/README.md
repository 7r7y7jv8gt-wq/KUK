# Scania S — complete Tridem lighting setup

[Download FS25_ScaniaS.zip](../FS25_ScaniaS.zip?raw=true) · [Validation](validation.json)

Adds the completed Tridem's lamp models, mounts, textures and lighting behaviour to all three supplied trucks: **4x2, 6x4 and 8x4**. Each keeps its original chassis, wheels, engine, coupling and animations.

| Fitted models, per truck | Lighting behaviour |
|---|---|
| 7 roof Briods + 4 bumper Briods | White engine-on DRL 80; native high beam 800; 1000 m range and 120° combined coverage |
| Optibeam blitzbar | Alternating amber flashes, 6 projectors at 100 m; independent steady engine-on cruise lights at 8 |
| 68 exterior diodes | Orange, first normal light stage, intensity 80 |
| 15 elongated lower-bar markers | Orange engine-on DRL, intensity 50 |
| 8 GeoVikings | Red guide lights, first normal light stage, intensity 20, both LODs |
| 4 rear FOR9T fixtures | Red DRL 20 at the first stage; white reverse light 50, 40 m projectors |
| 4 FOR9T work pods | Red DRL 20 at the first stage; white work light 50 on the third normal light stage, 60 m projectors |
| Scania griffin sign | Original artwork with steady red illumination |

The third normal F-key stage uses light types 0 1 2. Native high beam is separate, type 3, normally Ctrl+F. The blitzbar uses the native beacon switch and does not cast uncontrolled amber ground light while off.

The shorter chassis have adapted side-lamp spacing and their reverse lamps mounted at their own rear bumpers. The 8x4 uses two LED rows in the skirt gap between its steering axles. Fixture geometry is retained at its original size. The 8x4 also receives the rear work-lamp support bar that was absent from its source model.

New purchases select **Lamps Short**, **Goliath with lights**, **Schoch with lights** and backboard **Design 1** by default. Existing saved trucks retain their saved accessory choices: select these options in the shop to display the complete setup.

Replace the existing `FS25_ScaniaS.zip` in your mods folder with this ZIP, keep it zipped, and restart FS25. This is a separate package from `FS25_ScaniaS_Tridem.zip`.

The models load through native shared-light and beacon components. Original vehicle shape binaries and texture files are unchanged; the original Tridem lamp geometry and its required textures are bundled separately. Four incorrect PNG references per vehicle now point to the DDS files already supplied with the new trucks. GeoVikings retain the neutral dirt/gloss mask fallback used in the completed Tridem.

Checks passed for archive CRC, node mappings, native XML loading formats, material/texture/shape references, beam directions, quality-profile separation and configuration visibility. Each variant has 29 added main projectors and 6 beacon projectors. Original physics, engines, wheels, attachers and animations were preserved. **Not tested in FS25/GIANTS Editor; exact surface clearance and rendered appearance need an in-game check.**
