# KK25 Scania S Tridem — window-name shop option

Full mod: [`KK25_ScaniaS_Tridem_KRISTENSEN_EDIT.zip`](../KK25_ScaniaS_Tridem_KRISTENSEN_EDIT.zip), version **1.3.0.2**, built from the owner's latest three-part split ZIP.

The shop has a separate **Vindu navn** dropdown:

- **J. Kristensen** — default.
- **M. Kolbræk**.

Exactly one name appears in the owner's `Vindu navn` transform group. This is independent of the existing four **Name layout** door choices. The new option uses the free native `design13` slot and stable save IDs; no extra script is needed.

Both embedded window meshes now reference the original name DDS files already included under `decor/names/textures/`. Font, Norwegian flags, transparency and mipmaps are byte-identical to the owner-supplied originals. The model, window-name geometry and placements, shape binaries and all other original assets and vehicle settings are preserved.

Exit FS25 fully, replace **KK25_ScaniaS_Tridem_KRISTENSEN_EDIT.zip**, keep the filename, and restart. Open this truck in the shop/customization screen and select **Vindu navn**.

Checks passed for all 506 mappings, 1,024 node references, all local texture resources and ZIP CRC. Unchanged GIANTS Lua configuration readers executed in liblua5.4 recognize both selectable names and the J. Kristensen default. All four window-name switching transitions and 16 door/window combinations passed visibility checks. The native-reader harness mocks game services and XML lookup; **no live FS25 game or shop-GUI test was performed**.
