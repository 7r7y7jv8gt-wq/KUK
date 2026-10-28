# Volvo L90 — orange DRL and Scania-style Optibeam

[Download the complete FS25_volvoL90.zip](../FS25_volvoL90.zip?raw=true) · [Lighting code](LightingCode.xml) · [Validation](validation.json) · [Independent audit](audit.json)

**Version 1.0.0.4**, built from the owner's newer three-part RAR. The L90 Electric inherits the same lights; the original bucket and all original model binaries are included.

| Fitted lamps | Running/DRL function | Main function |
|---|---|---|
| 15 FOR9Ts | Orange engine-on guides, intensity 20, using their original orange atlas/UVs | White work lights, intensity 50, with separate low/high graphics projectors and 60 m coverage |
| 2 OZZ XP1s | Orange engine-on position guides, intensity 40 | White near beams 65 m / high beams 140 m, indicators and native amber strobes |
| Optibeam Dark Phantom | Separate orange engine-on cruise glow, intensity 8 | Same alternating double flash as the Scanias, intensity 12, six 100 m projected lights |

Front/forward-side FOR9Ts follow front work lights on the third normal F-key stage. Rear/back-side FOR9Ts follow rear work lights on the second stage. The normal high-beam control operates the OZZ high beams. The beacon switch operates the bar and OZZ strobes. The bar's cruise glow remains separate from its flashing/projected lights; DRLs do not illuminate the ground orange.

Seventeen obsolete stock shared-light loads were attached to nodes that the new lamps replaced. Those loads are removed, the side-marker references are corrected, and the replaced stock road projectors are explicitly disabled. Existing rear, brake, reverse, dashboard and factory beacon functions are preserved. Native light controls are used; no additional script or IC mod is needed.

Ten OZZ/bar texture references pointed to missing OneDrive files. Missing normal/dirt/gloss/glass maps now use neutral standard game assets. A small uniform amber map supplies the requested OZZ emission colour. **The missing original surface detail has not been recovered**, so those finishes may differ. Existing bundled textures and geometry are unchanged.

Exit FS25 completely, replace the old mod with this single `FS25_volvoL90.zip`, keep that exact filename, restart and select version **1.0.0.4**. The ZIP contains `modDesc.xml` directly at its root.

Checks passed for 762 unique scene nodes, 348 mappings, 717 main vehicle node references, local model resources, original binary identity, distinct low/high projectors and ZIP CRC. The original FOR9T orange atlas and OZZ UV channels were decoded and checked. An independent audit found every light controlled or explicitly hidden. **Not tested in the FS25 game runtime.**
