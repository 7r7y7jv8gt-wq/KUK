# Scania S 6x4 — four name layouts and front sign facing fix

[Download FS25_ScaniaS.zip](../FS25_ScaniaS.zip?raw=true) · [Artwork preview](ArtworkPreview.jpg) · [Name/IC code](NamesICCode.xml) · [Validation](validation.json)

**The original name lettering and Norwegian flags are restored.** Both name DDS files are copied byte for byte from the owner's supplied `FS25_Norske_Navnelogoer.zip`, at their original 2048 × 256 size, with transparency and mipmaps. No lettering, flags, colours or proportions were recreated. The four replacement transport-sign textures from the previous version remain included.

The **Name layout** shop option has four choices:

- J. Kristensen left / M. Kolbræk right (default).
- M. Kolbræk left / J. Kristensen right.
- J. Kristensen on the driver door only; passenger door blank.
- M. Kolbræk on the driver door only; passenger door blank.

Driver means vehicle left, at the existing driver name position. All four choices explicitly set both layouts and their name children, so switching choices clears the passenger door when required. Original name meshes, positions and flag textures are preserved.

The front GV604 cassette was facing the cab, putting its printed panels behind the opaque diffuser from the truck's front view. Its mounting rotation is corrected so the original printed faces point forward. Both outdoor IC click points retain their previous world positions. The grille sign uses **FS25_interactiveControl**: the left point opens/closes it; the right cycles **TUNG LAST → LANG LAST → BRED LAST** while open. Saved mode and multiplayer code are unchanged.

Replace `FS25_ScaniaS.zip` and restart FS25. Existing Briod high beams remain at 200 and white Briod DRLs at 40, with the 1000 m / 120° setup. Other lights, vehicle settings, binary geometry and the 4x2/8x4 variants are unchanged.

Checks passed for all 16 name configuration transitions, 603 mappings, 1025 checked node references, original DDS identity and archive CRC. An [independent sign audit](SignOrientationAudit.json) confirms the corrected depth ordering and unchanged click-point positions. **Not tested in FS25/GIANTS Editor; encoded mesh normals and the rendered folding appearance still need an in-game check.**
