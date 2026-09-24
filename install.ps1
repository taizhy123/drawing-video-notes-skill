[CmdletBinding()]
param(
    [switch]$WithoutAsr,
    [switch]$SkipSkillInstall
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw "未找到 Python。请安装 Python 3.10 或更高版本并重新打开 PowerShell。" }
$VersionText = & $Python.Source --version
if ($VersionText -notmatch "Python 3\.(1[0-9]|[2-9][0-9])") { throw "需要 Python 3.10 或更高版本；当前为 $VersionText。" }

Push-Location $ProjectRoot
try {
    if (-not (Test-Path ".venv")) { & $Python.Source -m venv .venv }
    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    & $VenvPython -m pip install --upgrade pip
    $Extras = if ($WithoutAsr) { ".[dev]" } else { ".[asr,dev]" }
    & $VenvPython -m pip install -e $Extras
    if (-not $SkipSkillInstall) {
        $SkillDestination = Join-Path $env:USERPROFILE ".codex\skills\art-course-notes"
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SkillDestination) | Out-Null
        Copy-Item (Join-Path $ProjectRoot "skill-source\art-course-notes") $SkillDestination -Recurse -Force
        Write-Host "Skill 已安装到 $SkillDestination"
    }
    Write-Host "安装完成。若尚未安装 FFmpeg，请先安装并重开终端，然后运行：.\.venv\Scripts\art-course-notes.exe check"
}
finally { Pop-Location }
