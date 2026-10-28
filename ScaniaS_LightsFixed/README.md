# Scania S Tridem — four name layouts, lights and red curtain

[Download FS25_ScaniaS_Tridem.zip](../FS25_ScaniaS_Tridem.zip?raw=true) · [Name configurations](NameCode.xml) · [Lighting code](LightingCode.xml) · [File validation](validation.json)

Built from the owner’s Tridem archive, including the two newly fitted exterior diodes, with the curtain copied from the latest Scania S 6x4. Replace the old ZIP in your mods folder, keep its filename unchanged, and restart FS25 completely. Keep the installed mod zipped.

The **Name layout** shop option now has the same four choices as the other Scania:

- J. Kristensen on the driver door / M. Kolbræk on the passenger door (default).
- M. Kolbræk on the driver door / J. Kristensen on the passenger door.
- J. Kristensen on the driver door only; passenger door blank.
- M. Kolbræk on the driver door only; passenger door blank.

Both original name logos and Norwegian flags are copied unchanged from the supplied prefab. They occupy the same door positions as on the other Scania. Name selection uses native shop configuration and needs no Interactive Control add-on. All 16 configuration transitions were checked; the original inline name geometry and both DDS files match the uploaded originals. [Independent name audit](NameAudit.json).

The original Scania S curtain is fitted with **Red curtain** as the first/default choice. The **Curtain** shop menu also offers brown, green, blue and no curtain. Existing trucks can select **Curtain → Red curtain** in the shop. The curtain model and all four textures are bundled with this ZIP. [Curtain configuration](CurtainCode.xml).

| Lamps | DRL / marker control | Main-light control |
|---|---|---|
| 68 exterior side diodes | Orange, stage 1, intensity 80 | Includes the two new diodes; all use identical controls |
| 15 elongated lower-bar markers | Orange engine-on DRL, intensity 50 | Steady; uses the existing “Schoch with lights” shop option |
| Scania griffin sign | Red illuminated artwork | Steady glow; retains its existing shop visibility option |
| Four rear FOR9Ts from pictures 1–2 | Red, stage 1, intensity 20 | White reverse lights, intensity 50, reverse gear; 40 m projectors |
| Four front-bumper Briods | White engine-on DRL, intensity 80 | Native high beam, intensity 800; 1000 m / 120° beam coverage |
| Four FOR9T work pods from picture 3 | Red, stage 1, intensity 20 | White work lights on the third normal F-key light stage; intensity 50, 60 m projectors |
| Eight Geovikings | Red guides, stage 1, intensity 20, both LODs | No additional work-light function requested |

The lower-bar markers use their supplied orange emissive material. Removed 11 old dashboard emitters that incorrectly targeted the rubber marker housings. The Scania sign uses the supplied grayscale artwork with a native red shader tint; the griffins, border and lettering remain intact. No DDS texture files were edited.

The third normal light stage is the final F-key step (types 0 1 2). Native high beam remains separate (type 3, normally Ctrl+F). Red DRLs remain on when the third stage is selected. All added projected lights start hidden and have distinct nodes for low/high graphics profiles.

Removed four stock work-lamp attachments behind the newly fitted FOR9T work pods. Corrected moved front-work and rear brake/indicator paths and removed references to stock reverse fixtures that were deleted in the new model. Other round rear lamps keep their normal brake, indicator and running-light functions.

The roof Briods retain the 1000 m / 120° setup, white DRL 80 and high-beam glow 800. The blitzbar retains 100 m alternating flash, independent steady cruise lights and no uncontrolled orange ground illumination. All 68 orange side diodes use the same stage-1 control at intensity 80.

The new GeoViking imports referenced original dirt/gloss masks and emissive textures outside the mod. Those originals were not included. Red/white emission now uses bundled textures; missing dirt/gloss masks use the game's neutral default mask, so the original dirt appearance may differ. No image or shape binary was edited.

The name update preserves all 1351 existing Tridem scene paths/IDs. The result has 1362 unique scene nodes, 503 valid mappings and 1015 checked XML node references. Only the main i3D and vehicle XML changed, with six name asset/configuration files and one text guide added. All existing lighting, curtain settings, shape binaries and gameplay data are preserved. Archive CRC passed. Live appearance has not been tested in FS25/GIANTS Editor.
