@echo off
setlocal
rem Read-only listing; no game files are modified or sent over the network.
powershell.exe -NoProfile -Command "$ErrorActionPreference = 'Stop'; $mapDataRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Farming Simulator 25\data'; if (-not (Test-Path -LiteralPath $mapDataRoot -PathType Container)) { $mapDataRoot = Read-Host 'Full path to FS25 data folder' }; if (-not (Test-Path -LiteralPath $mapDataRoot -PathType Container)) { Write-Error 'Folder not found'; exit 1 }; $mapDataRoot = (Get-Item -LiteralPath $mapDataRoot).FullName.TrimEnd([char]92); $mapCatalogOutput = Join-Path '%~dp0' 'FS25_asset_paths.txt'; $mapAssetList = @(Get-ChildItem -LiteralPath $mapDataRoot -Recurse -File -ErrorAction Stop | Where-Object { $_.Extension -in '.i3d','.xml','.dds','.png','.shapes' } | ForEach-Object { $_.FullName.Substring($mapDataRoot.Length + 1).Replace([char]92,[char]47) } | Sort-Object); if ($mapAssetList.Count -eq 0) { Write-Error 'No assets found'; exit 1 }; $mapAssetList | Set-Content -LiteralPath $mapCatalogOutput -Encoding UTF8; Write-Host ('Created FS25_asset_paths.txt: ' + $mapAssetList.Count + ' relative paths.')"
if errorlevel 1 (
 echo Could not create the list. Send a screenshot of this window.
) else (
 echo Upload FS25_asset_paths.txt to the chat.
)
pause
