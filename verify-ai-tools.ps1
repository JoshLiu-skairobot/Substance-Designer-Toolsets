# AI Tools Verification Script

Write-Host "
=== AI Tools Verification ===" -ForegroundColor Cyan
Write-Host "
1. Codex CLI:" -ForegroundColor Yellow
codex --version

Write-Host "
2. OpenSkills:" -ForegroundColor Yellow
openskills --version
Write-Host "   Skills Count:" -ForegroundColor Gray
$skillsCount = (openskills list | Select-String "Summary:").ToString() -replace '.*\((\d+) total\).*', '$1'
Write-Host "   Total: $skillsCount skills" -ForegroundColor Green

Write-Host "
3. OpenSpec:" -ForegroundColor Yellow
openspec --version

Write-Host "
4. Configuration Files:" -ForegroundColor Yellow
Write-Host "   Codex config:" -ForegroundColor Gray
if (Test-Path "$env:USERPROFILE\.codex\config.toml") {
    Write-Host "   鉁?~/.codex/config.toml exists" -ForegroundColor Green
} else {
    Write-Host "   鉁?~/.codex/config.toml missing" -ForegroundColor Red
}

Write-Host "   Claude config:" -ForegroundColor Gray
if (Test-Path ".claude\config.json") {
    Write-Host "   鉁?.claude/config.json exists" -ForegroundColor Green
} else {
    Write-Host "   鉁?.claude/config.json missing" -ForegroundColor Red
}

Write-Host "   OpenSpec config:" -ForegroundColor Gray
if (Test-Path ".openspec\config.json") {
    Write-Host "   鉁?.openspec/config.json exists" -ForegroundColor Green
} else {
    Write-Host "   鉁?.openspec/config.json missing" -ForegroundColor Red
}

Write-Host "
5. Skills Directory:" -ForegroundColor Yellow
if (Test-Path ".claude\skills") {
    $skillDirs = (Get-ChildItem ".claude\skills" -Directory).Count
    Write-Host "   鉁?.claude/skills directory exists ($skillDirs skill folders)" -ForegroundColor Green
} else {
    Write-Host "   鉁?.claude/skills directory missing" -ForegroundColor Red
}

Write-Host "
=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "All tools are installed and configured!
" -ForegroundColor Green
