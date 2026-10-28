# Scania S 6x4 — corrected front sign and outdoor IC

[Download FS25_ScaniaS.zip](../FS25_ScaniaS.zip?raw=true) · [Front-sign geometry preview](FrontSignPreview.jpg) · [Name/IC code](NamesICCode.xml) · [Validation](validation.json)

**Version 1.0.2.1.** Exit FS25 fully, replace the old `FS25_ScaniaS.zip` without changing its filename, and restart. Enable **FS25_interactiveControl** to use the sign controls.

**The original name lettering and Norwegian flags are restored.** Both name DDS files are copied byte for byte from the owner's supplied `FS25_Norske_Navnelogoer.zip`, at their original 2048 × 256 size, with transparency and mipmaps. No lettering, flags, colours or proportions were recreated. The four replacement transport-sign textures from the previous version remain included.

The **Name layout** shop option has four choices:

- J. Kristensen left / M. Kolbræk right (default).
- M. Kolbræk left / J. Kristensen right.
- J. Kristensen on the driver door only; passenger door blank.
- M. Kolbræk on the driver door only; passenger door blank.

Driver means vehicle left, at the existing driver name position. All four choices explicitly set both layouts and their name children, so switching choices clears the passenger door when required. Original name meshes, positions and flag textures are preserved.

The previous mounting flip exposed the cassette's opaque back plate. The actual FS25 mesh has now been decoded and checked: the printed front is restored, with upright lettering. The solid grey diffuser hides while the selected artwork is displayed, so it cannot cover the sign. The printed cards retain their original recessed positions inside the frame.

The lid is a small top cap. It now pivots about its actual top/rear edge, rather than folding around the centre of the cassette. The locks keep their original closed positions and move with the cap.

Stand in front of the truck and activate outdoor IC. Both points are on the **front lower corners**:

- **Left, looking at the truck:** open/close the cap and show/hide the sign.
- **Right, looking at the truck:** cycle **TUNG LAST → LANG LAST → BRED LAST** while open.

The closed face is intentionally blank; open it with the left point to reveal the selected panel. Saved mode and multiplayer logic are unchanged.

Replace `FS25_ScaniaS.zip` and restart FS25. Existing Briod high beams remain at 200 and white Briod DRLs at 40, with the 1000 m / 120° setup. Other lights, vehicle settings, binary geometry and the 4x2/8x4 variants are unchanged.

Checks passed for the decoded UV direction, recessed panel clearance, cap geometry, all three sign states, 604 mappings, 1027 checked node references and archive CRC. A [Blender preview](FrontSignPreview.jpg) uses the actual original meshes, bundled DDS and candidate transforms. The coloured IC dots in that preview are position markers, not game icons. [Independent IC audit](SignOrientationAudit.json) and [visual checks](FrontSignVisualValidation.json). **The mesh and native animation functions were checked, but this has not been tested in the FS25 game runtime.**
