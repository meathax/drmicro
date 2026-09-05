param([Parameter(ValueFromRemainingArguments=$true)][string[]]$TaskArgs)
$ErrorActionPreference = 'Stop'
$TaskPython = Get-Command python -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps'
if ($TaskPython) { $TaskPythonPath = $TaskPython.Source }
else {
    $TaskPythonPath = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (!(Test-Path -LiteralPath $TaskPythonPath)) { throw 'Python 3 is required. Run tools/dev.py with an available Python interpreter.' }
}
& $TaskPythonPath (Join-Path $PSScriptRoot 'dev.py') @TaskArgs
exit $LASTEXITCODE
