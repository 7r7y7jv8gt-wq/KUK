# Norske navnelogoer til FS25

[Last ned begge I3D-prefabene som ZIP](https://github.com/7r7y7jv8gt-wq/KUK/raw/refs/heads/codex/kk-maskin-logo-prefab/FS25_Norske_Navnelogoer.zip)

To separate transparente merker, begge med norsk flagg først og navnet på én linje:

| Navn på logoen | Fil som skal importeres |
| --- | --- |
| J.KRISTENSEN | `J_KRISTENSEN.i3d` |
| M.KOLBRÆK | `M_KOLBRAEK.i3d` |

Bokstaven Æ vises riktig på logoen; AE brukes bare i filnavnet. Begge har lik fysisk bokstavhøyde og flaggstørrelse.

Pakk ut ZIP-filen og kopier hele `FS25_Norske_Navnelogoer`-mappen inn i kjøretøyets modmappe. Importer ønsket I3D med **File > Import** i GIANTS Editor 10. Begge navn kan brukes samtidig. Behold `textures/` sammen med I3D-filene.

Standardflaten er 1 × 0,125 m. Skaler alle akser likt. Framsiden peker i lokal +Z-retning; plasser merket omtrent 1–3 mm utenfor kjøretøyets overflate. Kortere navn har mer transparent luft til høyre.

Inkluderer BC3/DXT5-teksturer med alpha og full mipmap-kjede, prefabDesc.xml, ikon, separate PNG-kilder og norsk importveiledning. Ingen kollisjon eller skyggekasting; geometri er innebygd i I3D-filene.

Filstruktur, geometri, teksturer, kontrollsummer og ZIP-integritet er kontrollert. Live import i GIANTS Editor 10 og FS25 er ikke testet her.

ZIP SHA-256: `f0bb126163a337e5274bf46b2eaedd829afaca6cdba70b55d55ba6c1b1a5ddf7`
