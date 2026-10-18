# Creates (or refreshes) the Monocat shortcuts on the Desktop and in the Start menu.
#   shortcuts.ps1          create or refresh both shortcuts
#   shortcuts.ps1 -Check   read only: exit 0 if both exist and point at this folder, 1 otherwise
param([switch]$Check)
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root 'Monocat.exe'
$shell = New-Object -ComObject WScript.Shell
$dirs = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
if ($Check) {
    foreach ($dir in $dirs) {
        $path = Join-Path $dir 'Monocat.lnk'
        if (-not (Test-Path -LiteralPath $path)) { exit 1 }
        if ($shell.CreateShortcut($path).TargetPath -ne $exe) { exit 1 }
    }
    exit 0
}
foreach ($dir in $dirs) {
    Remove-Item -LiteralPath (Join-Path $dir 'Mono Player.lnk') -ErrorAction SilentlyContinue
    $lnk = $shell.CreateShortcut((Join-Path $dir 'Monocat.lnk'))
    $lnk.TargetPath = $exe
    $lnk.WorkingDirectory = $root
    $lnk.IconLocation = (Join-Path $root 'assets\monocat.ico') + ',0'
    $lnk.Description = 'Monocat'
    $lnk.Save()
}
