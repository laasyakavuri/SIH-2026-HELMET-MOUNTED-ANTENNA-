 $ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Remove-Item *.zip -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter node_modules |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Get-ChildItem | Where-Object { $_.Name -ne '.git' -and $_.Name -ne 'bootstrap_sih.py' }) -DestinationPath sih-smart-helmet-complete.zip
Compress-Archive -Path ground-station -DestinationPath ground-station.zip
Compress-Archive -Path firmware -DestinationPath firmware.zip
Write-Host "Created: sih-smart-helmet-complete.zip, ground-station.zip, firmware.zip"
