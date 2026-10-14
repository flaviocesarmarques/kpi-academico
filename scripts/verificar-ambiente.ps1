# =============================================================================
# Diagnóstico do ambiente para a trilha DevOps — WINDOWS (PowerShell)
# -----------------------------------------------------------------------------
# No Windows, a trilha roda dentro do WSL2 (Ubuntu): o Makefile usa bash, e
# Docker, k3d e Ansible são ferramentas Linux. Este script verifica a base
# no Windows (WSL2, Docker Desktop, Git) e orienta a instalação.
# Depois, DENTRO do Ubuntu (WSL), rode: bash scripts/verificar-ambiente.sh
#
# Uso (PowerShell, na pasta do projeto):
#   powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1
# =============================================================================
$ErrorActionPreference = 'SilentlyContinue'
$pendencias = New-Object System.Collections.Generic.List[string]
$faltaObrigatorio = $false

function Ok($nome, $detalhe)   { Write-Host ("  [OK]    {0,-20} {1}" -f $nome, $detalhe) -ForegroundColor Green }
function Falta($nome, $detalhe, $instrucao, [bool]$obrigatorio = $true) {
  if ($obrigatorio) {
    Write-Host ("  [FALTA] {0,-20} {1}" -f $nome, $detalhe) -ForegroundColor Red
    $script:faltaObrigatorio = $true
  } else {
    Write-Host ("  [AVISO] {0,-20} {1}" -f $nome, $detalhe) -ForegroundColor Yellow
  }
  $script:pendencias.Add("${nome}: $instrucao")
}

Write-Host "Diagnóstico do ambiente — trilha DevOps kpi-academico (Windows)" -ForegroundColor Cyan
$so = Get-CimInstance Win32_OperatingSystem
Write-Host ("Sistema: {0} (build {1})" -f $so.Caption, $so.BuildNumber)

Write-Host "`nBase no Windows" -ForegroundColor Cyan

# --- WSL2 + Ubuntu -------------------------------------------------------------
$wslStatus = (wsl.exe --status 2>&1 | Out-String) -replace "`0", ''
if ($LASTEXITCODE -ne 0 -or -not $wslStatus) {
  Falta 'WSL2' 'não instalado' 'PowerShell como administrador: wsl --install -d Ubuntu  (reinicie o computador)'
} else {
  $distros = ((wsl.exe -l -v 2>&1 | Out-String) -replace "`0", '')
  if ($distros -match 'Ubuntu\S*\s+\w+\s+2') {
    Ok 'WSL2 + Ubuntu' 'instalado (versão 2)'
  } elseif ($distros -match 'Ubuntu') {
    Falta 'WSL2 + Ubuntu' 'Ubuntu está no WSL1' 'wsl --set-version Ubuntu 2'
  } else {
    Falta 'Ubuntu (WSL)' 'nenhuma distribuição Ubuntu' 'wsl --install -d Ubuntu'
  }
}

# --- Virtualização (requisito do WSL2 e do Docker) ------------------------------
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$hyper = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
if ($hyper -or $cpu.VirtualizationFirmwareEnabled) {
  Ok 'Virtualização' 'habilitada'
} else {
  Falta 'Virtualização' 'desabilitada na BIOS/UEFI' 'ative Intel VT-x / AMD-V na BIOS/UEFI do computador'
}

# --- Docker Desktop ---------------------------------------------------------------
$docker = Get-Command docker
if (-not $docker) {
  Falta 'Docker Desktop' 'não encontrado' 'winget install -e --id Docker.DockerDesktop  e depois Settings > Resources > WSL integration > Ubuntu'
} else {
  docker info *> $null
  if ($LASTEXITCODE -eq 0) { Ok 'Docker Desktop' ((docker --version) -replace 'Docker version ', '') }
  else { Falta 'Docker Desktop' 'instalado, mas parado' 'abra o Docker Desktop e aguarde "Engine running"' }
}

# --- Git e editor --------------------------------------------------------------------
if (Get-Command git) { Ok 'Git (Windows)' ((git --version) -replace 'git version ', '') }
else { Falta 'Git (Windows)' 'opcional: o Git do Ubuntu basta' 'winget install -e --id Git.Git' $false }

if (Get-Command code) { Ok 'VS Code' 'instalado (use a extensão WSL)' }
else { Falta 'VS Code' 'editor recomendado' 'winget install -e --id Microsoft.VisualStudioCode  + extensão "WSL"' $false }

# --- Recursos ------------------------------------------------------------------------
Write-Host "`nRecursos da máquina" -ForegroundColor Cyan
$memGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
$disco = Get-PSDrive -Name C
$discoGB = [math]::Round($disco.Free / 1GB)
if ($memGB -ge 16) { Ok 'Memória (RAM)' "$memGB GB" }
else { Falta 'Memória (RAM)' "$memGB GB (recomendado: 16 GB no Windows, 8 GB para o WSL)" 'em máquinas com 8 GB, faça as etapas 1–5 e desligue a observabilidade nas etapas 6–10' $false }
if ($discoGB -ge 30) { Ok 'Disco livre (C:)' "$discoGB GB" }
else { Falta 'Disco livre (C:)' "$discoGB GB (recomendado: 30 GB)" 'libere espaço no disco C:' $false }

# --- Resumo --------------------------------------------------------------------------
Write-Host "`nResumo" -ForegroundColor Cyan
if ($pendencias.Count -eq 0) {
  Write-Host '  Base do Windows pronta! Agora, no terminal Ubuntu (WSL):' -ForegroundColor Green
} else {
  Write-Host '  Instale o que falta:'
  foreach ($p in $pendencias) { Write-Host "   - $p" }
  Write-Host ''
  Write-Host '  Em seguida, no terminal Ubuntu (WSL):'
}
Write-Host '    cd ~ && git clone https://github.com/flaviocesarmarques/kpi-academico.git'
Write-Host '    cd kpi-academico && bash scripts/verificar-ambiente.sh'

if ($faltaObrigatorio) { exit 1 } else { exit 0 }
