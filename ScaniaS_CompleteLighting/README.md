# Scania S 6x4 — name layouts and front-sign IC

[Download FS25_ScaniaS.zip](../FS25_ScaniaS.zip?raw=true) · [Name/IC code](NamesICCode.xml) · [Validation](validation.json)

**Six original DDS textures are missing from the owner's upload. This download includes the full vehicle and the new code, but the name lettering and sign artwork will not display correctly until those images are added.** A notice and the required file paths are included in `README_NAMES_IC.txt` inside the ZIP.

The **Name layout** shop option has two choices:

- J. Kristensen left / M. Kolbræk right (default).
- M. Kolbræk left / J. Kristensen right.

The supplied name geometry and positions are preserved; the shop selection shows one complete layout at a time.

The new grille part is a GV604 folding transport sign. Enable **FS25_interactiveControl** to use its interactions. One click point opens/closes the sign; the other cycles **heavy → long → wide load** while it is open. A saved native analog IC controller stores the selected panel; a small server-authoritative helper cycles it. Only one load panel is visible at a time.

Add the owner's original images at these locations inside the mod to restore the artwork:

| Folder | Required files |
|---|---|
| `textures/names/` | `J_KRISTENSEN_diffuse.dds`, `M_KOLBRAEK_diffuse.dds` |
| `textures/gv604/` | `TUNG_LAST.dds`, `LANG_LAST.dds`, `BRED_LAST.dds`, `GVFlexiAdvertisment.dds` |

Replace `FS25_ScaniaS.zip` and restart FS25. Existing Briod high beams stay at 200, white Briod DRLs at 40, with the 1000 m / 120° setup. The other fitted lights and driving data are preserved. The supplied 4x2 and 8x4 remain unchanged.

Code checks passed for both name layouts, all 599 mappings and 999 checked node references. The Lua bridge was execution-tested for cycling, missing IC, initialization and client replay. Archive CRC passed. The six missing artwork files are explicitly recorded in validation.json. **Not tested in FS25/GIANTS Editor; the folding appearance needs an in-game check.**
