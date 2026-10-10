# John Deere 6030 lights — v0.3 repair candidate

The v0.1 FS25 game log confirmed a purchase/loading failure: TirePressure used
missing legacy helper functions, causing incomplete initialization and later
pressure/cleanup failures. The bundled game compatibility shader also failed
compilation at six float4-to-float3 assignments. Legacy vehicle sound template
names were unavailable.

v0.3 fixes those identified code issues: local nil/default and configuration
parsing helpers replace the removed globals; partly initialized vehicle cleanup
is guarded; the sound set uses the installed FS25 John Deere series6M sound XML.
A mod-local copy of the supplied shader explicitly selects .xyz at the six failing
samples and resolves its three default texture arrays through FS25 data paths.
Every packaged model using that compatibility shader now refers to the local
copy. No other shader code was changed. The user's installed game files and
original FS22 archive are unchanged. The supplied shader source is retained at
source/FS25_vehicleShader_original.xml.

Passed: 45 XML/I3D files parse; 336 external resource references resolve against
the supplied catalog; 514 local file references resolve; 44 light node references
resolve; original geometry, scene ordering and light-state/strobe wiring unchanged;
ZIP CRC; isolated Lua 5.1 regression tests without legacy globals, including load,
configuration selection, pressure bounds, friction, savegame pressure, parser
behavior and failed-load cleanup. Shader source exactly matches the expected six
RGB selections and three default texture-path changes.

Not run: FS25 shader compilation, vehicle purchase, lighting, driving, collision,
attachment, refilling and multiplayer tests. The new candidate requires another
FS25 test; these static checks do not prove that the purchase now succeeds.

Install: remove the old test ZIP and any extracted copy from the FS25 mods folder.
Put FS25_JohnDeere_6030_Lights_Test_v03.zip there WITHOUT extracting it; enable the
new candidate in a test save, try to buy it and test lights/HOME-key strobes.
Return a fresh game log.txt if loading still fails.

Output generator: tools/convert_tractor.py; validator: tools/validate_candidate.py.
The generator overwrites its generated output folder/ZIP, so preserve any user
edits before intentionally rebuilding. No services need startup. Existing source,
asset catalog, Python/Pillow and retained Lupa 2.8 Lua 5.1 dependencies are used.

Candidate SHA256: cfa1b580b1f6ea86fa2078840e68ce4cfb81758185c4bd8476787c361daa4d42
