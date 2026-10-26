# Scania S Tridem — fjernlys og blitz rettet

[Last ned FS25_ScaniaS_Tridem.zip](../FS25_ScaniaS_Tridem.zip?raw=true) · [Se lyskoden](LightingCode.xml)

Erstatt den gamle ZIP-filen i mods-mappen, behold filnavnet og start FS25 helt på nytt. ZIP-filen skal ikke pakkes ut i mods-mappen.

Briodenes hovedlys følger nå bilens egen fjernlysbryter (`lightTypes="3"`, normalt Ctrl+F), med intensitet 800. De følger ikke arbeidslystrinnene 1/2. Motorstyrte hvite DRL forblir på 80. Bilens vanlige fjernlys og begge grafikkprofilene bruker samme fjernlysgruppe.

Bjelkas blitz er koblet til varsellysbryteren. Tre lyskastere på hver side og de to blitzmeshene bruker den opprinnelige bjelkas shader og oransje lys. Venstre og høyre side dobbeltblinker vekselvis. Alle seks lyskasterne har visibility=false som grunninnstilling og blir styrt av beacon-koden, slik at bjelka ikke legger konstant oransje lys på bakken når blitzene er av. Cruiselysene er separat motorstyrt på intensitet 8 og lyser fast i selve bjelka; de har ingen lyskaster som belyser bakken.

Alle tidligere teksturreparasjoner og 66 oransje sidedioder er beholdt. Mesh- og teksturbinariene er uendret. Referansefilen med lyskoden er allerede installert i bilens XML.

Kontrollert: 385 nodemappinger, 776 XML-nodereferanser, fjernlysgrupper, DRL-styring, alle seks blitzlyskastere, blinkfaser og ZIP-kontrollsum. Ikke testet i FS25/GIANTS Editor.

Kilder for native styring: [GIANTS Lights](https://gdn.giants-software.com/documentation_scripting_fs25.php?version=engine&category=78&class=691), [GIANTS BeaconLight](https://gdn.giants-software.com/documentation_scripting_fs25.php?version=engine&category=14&class=165).
