#!/usr/bin/env pwsh
# ===========================================
# SCRIPT DE DEPLOY AUTOMATIZADO PARA VERCEL
# SaaS Controle Financeiro
# ===========================================

Write-Host "🚀 Iniciando deploy para Vercel..." -ForegroundColor Green
Write-Host "" 

# Verificar se estamos em um repositório Git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Erro: Este diretório não é um repositório Git!" -ForegroundColor Red
    Write-Host "Execute: git init" -ForegroundColor Yellow
    exit 1
}

# Verificar se há mudanças não commitadas
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 Detectadas mudanças não commitadas..." -ForegroundColor Yellow
    Write-Host "Arquivos modificados:"
    git status --short
    Write-Host ""
    
    $commit = Read-Host "Deseja fazer commit das mudanças? (s/N)"
    if ($commit -eq "s" -or $commit -eq "S") {
        $message = Read-Host "Digite a mensagem do commit"
        if (-not $message) {
            $message = "Deploy to Vercel - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        }
        
        Write-Host "📦 Fazendo commit..." -ForegroundColor Blue
        git add .
        git commit -m "$message"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erro ao fazer commit!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "⚠️  Continuando sem commit..." -ForegroundColor Yellow
    }
}

# Verificar branch atual
$currentBranch = git branch --show-current
Write-Host "📍 Branch atual: $currentBranch" -ForegroundColor Cyan

if ($currentBranch -ne "main" -and $currentBranch -ne "master") {
    Write-Host "⚠️  Você não está na branch main/master!" -ForegroundColor Yellow
    $continue = Read-Host "Deseja continuar mesmo assim? (s/N)"
    if ($continue -ne "s" -and $continue -ne "S") {
        Write-Host "❌ Deploy cancelado!" -ForegroundColor Red
        exit 1
    }
}

# Push para o repositório
Write-Host "📤 Fazendo push para o repositório..." -ForegroundColor Blue
git push origin $currentBranch

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao fazer push!" -ForegroundColor Red
    Write-Host "Verifique se o repositório remoto está configurado corretamente." -ForegroundColor Yellow
    exit 1
}

# Verificar se o Vercel CLI está instalado
Write-Host "🔍 Verificando Vercel CLI..." -ForegroundColor Blue
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue

if (-not $vercelInstalled) {
    Write-Host "⚠️  Vercel CLI não encontrado!" -ForegroundColor Yellow
    $install = Read-Host "Deseja instalar o Vercel CLI? (s/N)"
    if ($install -eq "s" -or $install -eq "S") {
        Write-Host "📦 Instalando Vercel CLI..." -ForegroundColor Blue
        npm install -g vercel
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erro ao instalar Vercel CLI!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "ℹ️  Você pode instalar manualmente com: npm install -g vercel" -ForegroundColor Cyan
        Write-Host "📖 Consulte o arquivo DEPLOY_VERCEL.md para instruções completas." -ForegroundColor Cyan
        exit 0
    }
}

# Verificar se está logado no Vercel
Write-Host "🔐 Verificando autenticação no Vercel..." -ForegroundColor Blue
$vercelAuth = vercel whoami 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Não está logado no Vercel!" -ForegroundColor Yellow
    $login = Read-Host "Deseja fazer login agora? (s/N)"
    if ($login -eq "s" -or $login -eq "S") {
        Write-Host "🔑 Fazendo login no Vercel..." -ForegroundColor Blue
        vercel login
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erro ao fazer login!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "ℹ️  Você pode fazer login manualmente com: vercel login" -ForegroundColor Cyan
        exit 0
    }
} else {
    Write-Host "✅ Logado como: $vercelAuth" -ForegroundColor Green
}

# Verificar arquivos de configuração
Write-Host "📋 Verificando arquivos de configuração..." -ForegroundColor Blue

$configFiles = @(
    "vercel.json",
    "frontend/package.json",
    "backend/requirements.txt",
    "backend/main.py"
)

$missingFiles = @()
foreach ($file in $configFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Arquivos de configuração em falta:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    Write-Host "📖 Consulte o arquivo DEPLOY_VERCEL.md para instruções." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Todos os arquivos de configuração encontrados!" -ForegroundColor Green

# Fazer deploy
Write-Host "" 
Write-Host "🚀 Iniciando deploy no Vercel..." -ForegroundColor Green
Write-Host "" 

# Verificar se já existe um projeto
$existingProject = vercel ls 2>$null | Select-String (Split-Path -Leaf (Get-Location))

if ($existingProject) {
    Write-Host "📦 Projeto existente encontrado. Fazendo deploy..." -ForegroundColor Blue
    vercel --prod
} else {
    Write-Host "🆕 Novo projeto. Configurando..." -ForegroundColor Blue
    vercel --prod
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "🎉 Deploy concluído com sucesso!" -ForegroundColor Green
    Write-Host "" 
    
    # Obter URL do projeto
    $projectUrl = vercel ls --scope $(vercel whoami) | Select-String "https://" | ForEach-Object { $_.ToString().Trim() }
    
    if ($projectUrl) {
        Write-Host "🌐 URL da aplicação: $projectUrl" -ForegroundColor Cyan
        Write-Host "" 
    }
    
    Write-Host "📊 Próximos passos:" -ForegroundColor Yellow
    Write-Host "   1. Configurar variáveis de ambiente no painel do Vercel" -ForegroundColor White
    Write-Host "   2. Configurar banco de dados Neon" -ForegroundColor White
    Write-Host "   3. Testar a aplicação" -ForegroundColor White
    Write-Host "   4. Configurar domínio personalizado (opcional)" -ForegroundColor White
    Write-Host "" 
    Write-Host "📖 Consulte DEPLOY_VERCEL.md para instruções detalhadas." -ForegroundColor Cyan
    
} else {
    Write-Host "" 
    Write-Host "❌ Erro durante o deploy!" -ForegroundColor Red
    Write-Host "" 
    Write-Host "🔍 Possíveis soluções:" -ForegroundColor Yellow
    Write-Host "   1. Verificar logs no painel do Vercel" -ForegroundColor White
    Write-Host "   2. Verificar configurações no vercel.json" -ForegroundColor White
    Write-Host "   3. Verificar variáveis de ambiente" -ForegroundColor White
    Write-Host "   4. Consultar DEPLOY_VERCEL.md" -ForegroundColor White
    Write-Host "" 
    exit 1
}

Write-Host "" 
Write-Host "✨ Script de deploy finalizado!" -ForegroundColor Green
Write-Host ""