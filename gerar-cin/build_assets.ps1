$bytes1 = [System.IO.File]::ReadAllBytes("$PSScriptRoot\img (1).jfif")
$b64_1 = [System.Convert]::ToBase64String($bytes1)

$bytes2 = [System.IO.File]::ReadAllBytes("$PSScriptRoot\img (2).jfif")
$b64_2 = [System.Convert]::ToBase64String($bytes2)

$content = @"
window.CIN_BG_FRENTE = "data:image/jpeg;base64,$b64_1";
window.CIN_BG_VERSO = "data:image/jpeg;base64,$b64_2";
"@

[System.IO.File]::WriteAllText("$PSScriptRoot\assets.js", $content, [System.Text.Encoding]::UTF8)
Write-Output "assets.js generated with size: $( (Get-Item "$PSScriptRoot\assets.js").Length ) bytes"
