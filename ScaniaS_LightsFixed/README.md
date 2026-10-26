# Scania S Tridem — wider Briod beams

[Download FS25_ScaniaS_Tridem.zip](../FS25_ScaniaS_Tridem.zip?raw=true) · [View lighting code](LightingCode.xml)

Replace the old ZIP in your mods folder, keep the filename unchanged, and restart FS25 completely. Keep the installed mod zipped.

The Briod lights now cover approximately 120 degrees across the front, compared with the previous 20-degree beam. In the high graphics profile, each lamp has a 60-degree cone and the beams fan outward by 0, ±10, ±20, and ±30 degrees. The low graphics profile uses one 120-degree beam. Drop-off is reduced from 2 to 1 for softer coverage. The projectors still face forward.

| Setting | Value |
|---|---|
| Briod projected-light range | 1000 metres |
| Briod main glow | 800, controlled by native high beam (normally Ctrl+F) |
| Engine-on white DRLs | 80 |
| Blitzbar projected-light range | 100 metres |
| Cruise lights | 8, steady engine-on |

The blitzbar retains its alternating double flash and starts with all six projected lights off, so the uncontrolled orange ground light stays fixed. All prior texture repairs and 66 orange side diodes are preserved.

Validation confirmed that only cone angle, yaw, and drop-off changed on the eight Briod projector nodes. Vehicle XML, controls, materials, texture images, shape binaries, all node IDs, and all index paths remain unchanged. Archive CRC passed. Live appearance has not been tested in FS25/GIANTS Editor.
