# Beltegående skogsvinsj – fotobasert 3D-modell

Modellert etter de tre bildene av den kantede, grønne T-WINCH-maskinen. Det første bildet viser et annet, avrundet motorhus og er ikke hovedreferansen.

Åpne `model/TWINCH_forestry_winch.blend` i Blender 4.3 eller nyere. GLB, FBX og OBJ/MTL følger med for andre 3D-programmer. Materialene er inkludert; eksterne teksturbilder er ikke nødvendige. Behold OBJ og MTL i samme mappe. Ved OBJ-import: Z opp, front −Y.

Modellen har separate grupper for chassis, venstre og høyre belte, motorhus, skjær, hydraulikk, vinsjtrommel, kabelføring og lys/dekor. Ventilasjonsåpninger, beltesko, ruller, vinsjtrommel, hydraulikksylindre, arbeidslys, varsellys og brannslukker er modellert. Skjæret har et eget dreiepunkt. Delene er ikke animert.

Enheter: meter. Omtrentlige yttermål: 3,12 m bredde, 3,93 m lengde og 3,19 m høyde inkludert mast. Mål og detaljer er anslått fra bildene, ikke fabrikktegninger. Dette er en visuell modell, ikke et mekanisk konstruksjonsunderlag.

Dette er et 3D-objekt, ikke en spillklar FS25-mod. Bruk i FS25 krever import i GIANTS Editor, I3D-oppsett, kollisjon, kjøretøy-XML, materialtilpasning og testing av belter, vinsj og lys i spillet.

`previews/` inneholder to forhåndsvisninger. `model_report.json` viser modellstatistikk. `export_validation.json` dokumenterer at alle fire formater ble åpnet på nytt i Blender. `create_twinch.py` er det redigerbare byggeskriptet (utdatamappen kan tilpasses øverst i filen).
