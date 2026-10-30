# Scania — feilrettede pakker 30.10.2026

[Last ned samlepakken med alle fire rettede modpakker](https://media.githubusercontent.com/media/7r7y7jv8gt-wq/KUK/main/downloads/Scania_Feilrettet_20261030.zip).

Pakk samlepakken ut utenfor mods-mappa. Kopier de tre ZIP-filene fra **1_MODDER_FRA_LOGGEN** til mods-mappa, erstatt de gamle og start FS25 på nytt. Den eldre Tridem ligger separat i **2_ELDRE_TRIDEM_VALGFRI**.

| Mod | Versjon | Separat komplett ZIP |
|---|---|---|
| Scania S 4x2 / 6x4 / 8x4 | 1.0.2.3 | [KK25_ScaniaS_KRISTENSEN_EDIT.zip](../KK25_ScaniaS_KRISTENSEN_EDIT.zip) |
| KK25 Tridem, nye vindusnavn | 1.3.0.4 | [KK25_ScaniaS_Tridem_KRISTENSEN_EDIT.zip](../KK25_ScaniaS_Tridem_KRISTENSEN_EDIT.zip) |
| Bergaas tippbil og hengere | 1.0.0.5 | [FS25_BergaasDesign_Scania_Tipper_Pack.zip](../FS25_BergaasDesign_Scania_Tipper_Pack.zip) |
| Eldre FS25 Tridem | 1.3.0.3 | [FS25_ScaniaS_Tridem.zip](../FS25_ScaniaS_Tridem.zip) |

Den opprinnelige [FS25_ScaniaS.zip](../FS25_ScaniaS.zip) er også oppdatert med samme innhold som KK25 S-pakken. Bruk filnavnet du allerede har; loggen bruker KK25-navnet. Ingen gamle navnevalg er lagt tilbake i KK25 Tridem.

## Rettet

- **S-pakken:** rå 800×600-oransjetekstur er erstattet i ressurskoblingen med eksisterende identisk oransje DDS med mipnivåer. Native fjernlys- og arbeidslyskanaler i 4x2/8x4 er samordnet. Motoreffekt i butikkmetadata er gjort numerisk; alle motorvalg og effekter er bevart.
- **Begge Tridem-pakkene:** skjulte gardinholdere har egne synlige lastemounts; alle fargene kan lastes. Doble lysrøtter i LOW/HIGH har egne identiske LOW-kopier, skjulte underlys er rettet, ubrukte editorobjekter er bevart skjult under kjøretøyet, teli-ikonet og doble vektormellomrom er rettet. Hooklift-Lua har korrekt skjema, handlingstabell og flerspillerhendelse. Blinkflatene bruker native dobbelblink og samme aktiveringsintensitet for alle UV-kanaler. Shaderens stockbilder har absolutte game-referanser. Oransje kart og butikkikon bruker DDS med mipnivåer.
- **Bergaas:** manglende valgfri lysutvidelse er registrert bare når den finnes, TerraFarm-integrasjon er bevart valgfritt, doble arvede spesialiseringer er rettet, og alle tre tippeanimasjoner har fått samlet tidslinje uten tap av deler/tider. Merke og trailernavn er registrert riktig. Sju shader-fallbackbilder peker til game-mappa. Glass/oransje/grå kart har gyldige potens-av-to DDS-filer med mipnivåer. De tre genererte blink-/navnemodellene bruker igjen inline-formatet.
- **Lys-/navnemodeller, siste retting:** den eksterne binærkonverteringen i forrige pakke ga en native feil der blinknoden ikke ble en Shape. Alle fem konverterte modeller er tilbakeført til tidligere inline-format: Bergaas **1.0.0.5**, eldre FS Tridem **1.3.0.3**. Meshdata, materialer, shaderstier, nodebaner og øvrige rettinger beholdes. Bare de fem egenlagde binærfilene er fjernet. Inline-ytelsesadvarslene kan derfor vises igjen.

Originale hovedmodeller, opprinnelige shape-binarier, lysintensiteter, plasseringer, konfigurasjonsvalg og originale navneteksturer/flagg er bevart. Originale PNG/DDS-filer ligger fortsatt i pakkene; rettede ressurskoblinger bruker egnede DDS-filer.

## Kontroll og begrensninger

Åtte kjøretøy, 47 I3D-modeller og **5 339 nodereferanser** er kontrollert i den foregående rettingen. De øvrige feilrettingene er byte-identiske i denne oppdateringen. Fem modeller er nå kontrollert uavhengig mot tidligere inline-innhold: FP32-posisjoner, normaler, UV-er, indekser, delsett, grenser og Shape-ID-er stemmer, og all XML utenfor Shapes er uendret. Hver ZIP er CRC-kontrollert, og hver fil samsvarer med den kontrollerte kandidaten.

Den tidligere binærrundreisen viste bare at egne kodere og dekodere var enige. Den dokumenterte ikke at FS25 kunne laste filene. Brukerens skjermbilde viste at dette feilet, og den konverteringen er derfor tilbakeført. De historiske binærrapportene er merket som trukket tilbake.

**Ingen ny FS25-kjøring eller full GIANTS-shaderkompilering er utført.** Inline-modellene kan gi ytelsesadvarsler, og en **konsolladvarsel om størrelsen på Bergaas' opprinnelige mesh 48** gjenstår. De andre Scania-rettingene er beholdt. Loggens feil i andre modder er separate fra denne pakken.

[Manifest og kontrollsummer](Manifest.json) · [Tilbakeføringskontroll](InlineRollbackValidation.json) · [Bergaas](Bergaas_RestoredModelValidation.json) · [Installasjon](LES_MEG.txt). Brukerens rå spillogg er ikke publisert.
