# Exit code 1 if this copy of Monocat is running (its files are in use), 0 otherwise.
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv\Scripts'
$procs = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe' OR Name='Monocat.exe'" -ErrorAction SilentlyContinue
foreach ($p in $procs) {
    if ($p.ProcessId -eq $PID) { continue }
    $cmd = [string]$p.CommandLine
    $exe = [string]$p.ExecutablePath
    if ($exe -like "$root*" -or $cmd -like "*$venv*" -or $cmd -like "*$root\main.py*") { exit 1 }
}
exit 0
