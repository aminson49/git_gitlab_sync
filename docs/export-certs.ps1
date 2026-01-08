$stores = @(
    @{Location='LocalMachine'; Name='Root'},
    @{Location='LocalMachine'; Name='CA'},
    @{Location='CurrentUser'; Name='Root'},
    @{Location='CurrentUser'; Name='CA'}
)

$outputFile = "$env:USERPROFILE\ca-bundle.crt"
if (Test-Path $outputFile) { Remove-Item $outputFile }

foreach ($storeInfo in $stores) {
    $storePath = "Cert:\$($storeInfo.Location)\$($storeInfo.Name)"
    Write-Host "Exporting from $storePath..."
    $certs = Get-ChildItem -Path $storePath -ErrorAction SilentlyContinue
    foreach ($cert in $certs) {
        $pem = "-----BEGIN CERTIFICATE-----`n$([Convert]::ToBase64String($cert.RawData, 'InsertLineBreaks'))`n-----END CERTIFICATE-----`n"
        Add-Content -Path $outputFile -Value $pem
    }
}

Write-Host "Export complete: $outputFile"
