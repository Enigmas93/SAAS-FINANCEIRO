# Script PowerShell para Deploy no Render
# Execute este script para preparar e fazer deploy do projeto

Write-Host "🚀 Iniciando processo de deploy para o Render..." -ForegroundColor Green

# Verificar se estamos em um repositório Git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Erro: Este não é um repositório Git. Execute 'git init' primeiro." -ForegroundColor Red
    exit 1
}

# Verificar se há mudanças não commitadas
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 Detectadas mudanças não commitadas. Fazendo commit..." -ForegroundColor Yellow
    
    # Adicionar todos os arquivos
    git add .
    
    # Fazer commit
    $commitMessage = Read-Host "Digite a mensagem do commit (ou pressione Enter para usar mensagem padrão)"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "feat: configurações de deploy para Render - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    
    git commit -m $commitMessage
    Write-Host "✅ Commit realizado: $commitMessage" -ForegroundColor Green
}

# Verificar branch atual
$currentBranch = git branch --show-current
Write-Host "📍 Branch atual: $currentBranch" -ForegroundColor Cyan

if ($currentBranch -ne "main" -and $currentBranch -ne "master") {
    $switchBranch = Read-Host "Você está na branch '$currentBranch'. Deseja mudar para 'main'? (y/N)"
    if ($switchBranch -eq "y" -or $switchBranch -eq "Y") {
        git checkout main
        Write-Host "✅ Mudou para branch main" -ForegroundColor Green
    }
}

# Push para o repositório
Write-Host "📤 Fazendo push para o repositório..." -ForegroundColor Yellow
try {
    git push origin $currentBranch
    Write-Host "✅ Push realizado com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro no push. Verifique suas credenciais e conexão." -ForegroundColor Red
    Write-Host "Erro: $_" -ForegroundColor Red
    exit 1
}

# Verificar arquivos de configuração
Write-Host "🔍 Verificando arquivos de configuração..." -ForegroundColor Yellow

$configFiles = @(
    "render.yaml",
    "backend/Dockerfile",
    "backend/requirements.txt",
    "frontend/package.json",
    ".env.production",
    "frontend/.env.production",
    "DEPLOY_RENDER.md"
)

$missingFiles = @()
foreach ($file in $configFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Arquivos de configuração ausentes:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "✅ Todos os arquivos de configuração estão presentes!" -ForegroundColor Green
}

# Mostrar próximos passos
Write-Host "`n🎯 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Acesse: https://dashboard.render.com" -ForegroundColor White
Write-Host "2. Clique em 'New +' → 'Blueprint'" -ForegroundColor White
Write-Host "3. Conecte seu repositório GitHub" -ForegroundColor White
Write-Host "4. Selecione este repositório" -ForegroundColor White
Write-Host "5. O Render detectará automaticamente o arquivo render.yaml" -ForegroundColor White
Write-Host "6. Clique em 'Apply' para iniciar o deploy" -ForegroundColor White

Write-Host "`n📋 INFORMAÇÕES DO PROJETO:" -ForegroundColor Cyan
Write-Host "   - Nome do Backend: saas-financeiro-backend" -ForegroundColor White
Write-Host "   - Nome do Frontend: saas-financeiro-frontend" -ForegroundColor White
Write-Host "   - Nome do Database: saas-financeiro-db" -ForegroundColor White
Write-Host "   - Health Check: /health" -ForegroundColor White
Write-Host "   - Documentação API: /docs" -ForegroundColor White

Write-Host "`n📖 Para mais detalhes, consulte: DEPLOY_RENDER.md" -ForegroundColor Yellow

Write-Host "`n🎉 Projeto preparado para deploy! Siga os próximos passos no Render." -ForegroundColor Green

# Abrir documentação se solicitado
$openDocs = Read-Host "`nDeseja abrir a documentação de deploy? (y/N)"
if ($openDocs -eq "y" -or $openDocs -eq "Y") {
    if (Test-Path "DEPLOY_RENDER.md") {
        Start-Process "DEPLOY_RENDER.md"
    }
}

# Abrir Render Dashboard se solicitado
$openRender = Read-Host "Deseja abrir o Render Dashboard? (y/N)"
if ($openRender -eq "y" -or $openRender -eq "Y") {
    Start-Process "https://dashboard.render.com"
}

Write-Host "`n✨ Deploy script concluído!" -ForegroundColor Green