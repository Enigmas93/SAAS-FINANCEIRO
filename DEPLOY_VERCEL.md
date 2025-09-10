# 🚀 Deploy no Vercel - SaaS Controle Financeiro

Guia completo para fazer deploy da aplicação SaaS de Controle Financeiro no Vercel.

## 📋 Pré-requisitos

- [ ] Conta no [Vercel](https://vercel.com)
- [ ] Conta no [Neon](https://neon.tech) para banco PostgreSQL
- [ ] Repositório Git (GitHub, GitLab ou Bitbucket)
- [ ] Node.js 18+ instalado localmente
- [ ] Python 3.11+ instalado localmente

## 🗄️ 1. Configuração do Banco de Dados (Neon)

### 1.1 Criar Projeto no Neon

1. Acesse [Neon Console](https://console.neon.tech)
2. Clique em "Create Project"
3. Configure:
   - **Project Name**: `saas-financeiro`
   - **Database Name**: `saas_financeiro`
   - **Region**: Escolha a mais próxima dos usuários
4. Anote a **Connection String** gerada

### 1.2 Configurar Tabelas

```sql
-- Execute no Neon SQL Editor
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Suas tabelas serão criadas automaticamente pelo SQLAlchemy
-- quando a aplicação for executada pela primeira vez
```

## 🔧 2. Preparação do Repositório

### 2.1 Verificar Estrutura

```
saas-controle-financeiro/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.production
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── models/
├── vercel.json
└── .env.production
```

### 2.2 Commit e Push

```bash
git add .
git commit -m "Configure for Vercel deployment"
git push origin main
```

## 🚀 3. Deploy no Vercel

### 3.1 Importar Projeto

1. Acesse [Vercel Dashboard](https://vercel.com/dashboard)
2. Clique em "New Project"
3. Conecte seu repositório Git
4. Selecione o repositório `saas-controle-financeiro`

### 3.2 Configurações de Build

**Framework Preset**: `Create React App`

**Build Settings** (configuradas automaticamente via vercel.json):
- **Build Command**: `cd frontend && npm run build`
- **Output Directory**: `frontend/build`
- **Install Command**: `npm install` (automático)

### 3.3 Variáveis de Ambiente

No painel do Vercel, adicione as seguintes variáveis:

#### Backend/API
```env
DATABASE_URL=postgresql://username:password@hostname:port/database_name?sslmode=require
SECRET_KEY=your-super-secret-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=false
```

#### Frontend
```env
REACT_APP_API_URL=https://your-app-name.vercel.app/api
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

#### Stripe (Pagamentos)
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### Email (Opcional)
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3.4 Deploy

1. Clique em "Deploy"
2. Aguarde o build completar (3-5 minutos)
3. Acesse a URL gerada: `https://your-app-name.vercel.app`

## 🔧 4. Configurações Avançadas

### 4.1 Domínio Customizado

1. No painel do Vercel, vá em "Settings" > "Domains"
2. Adicione seu domínio personalizado
3. Configure os DNS conforme instruções

### 4.2 Configurações de Performance

```json
// vercel.json - já configurado
{
  "functions": {
    "backend/main.py": {
      "runtime": "python3.11",
      "maxDuration": 30
    }
  }
}
```

### 4.3 Monitoramento

- **Analytics**: Habilitado automaticamente
- **Speed Insights**: Disponível no painel
- **Logs**: Acesse em "Functions" > "View Function Logs"

## 🔒 5. Segurança

### 5.1 Variáveis Sensíveis

- ✅ Todas as chaves estão em variáveis de ambiente
- ✅ SSL/TLS habilitado automaticamente
- ✅ CORS configurado corretamente

### 5.2 Headers de Segurança

```json
// Já configurado no vercel.json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        }
      ]
    }
  ]
}
```

## 📊 6. Monitoramento e Logs

### 6.1 Acessar Logs

1. Vercel Dashboard > Seu Projeto
2. Aba "Functions"
3. Clique em "View Function Logs"

### 6.2 Métricas

- **Performance**: Speed Insights
- **Uso**: Analytics
- **Erros**: Function Logs

## 🔄 7. CI/CD Automático

### 7.1 Deploy Automático

- ✅ Push para `main` → Deploy automático
- ✅ Pull Requests → Preview deployments
- ✅ Rollback com um clique

### 7.2 Ambientes

- **Production**: Branch `main`
- **Preview**: Pull Requests
- **Development**: Branch `develop` (opcional)

## 🛠️ 8. Troubleshooting

### 8.1 Problemas Comuns

**Build falha**:
```bash
# Verificar logs no Vercel Dashboard
# Comum: dependências em falta
cd frontend && npm install
```

**API não responde**:
- Verificar variáveis de ambiente
- Verificar logs da função
- Testar endpoint: `https://your-app.vercel.app/api/health`

**Banco não conecta**:
- Verificar `DATABASE_URL`
- Verificar se Neon está ativo
- Verificar SSL mode

### 8.2 Comandos Úteis

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy local
vercel

# Ver logs
vercel logs

# Listar deployments
vercel ls
```

## 💰 9. Custos

### 9.1 Vercel
- **Hobby**: Grátis (100GB bandwidth/mês)
- **Pro**: $20/mês (1TB bandwidth/mês)

### 9.2 Neon
- **Free**: Grátis (0.5GB storage)
- **Pro**: $19/mês (10GB storage)

## 🎯 10. Próximos Passos

1. ✅ **Configurar domínio personalizado**
2. ✅ **Configurar monitoramento avançado**
3. ✅ **Implementar backup automático**
4. ✅ **Configurar alertas**
5. ✅ **Otimizar performance**

## 📞 Suporte

- **Vercel**: [Documentação](https://vercel.com/docs)
- **Neon**: [Documentação](https://neon.tech/docs)
- **Issues**: Criar issue no repositório

---

## 🚀 Deploy Rápido

```bash
# 1. Preparar repositório
git add .
git commit -m "Deploy to Vercel"
git push origin main

# 2. Importar no Vercel
# - Acesse vercel.com/new
# - Conecte o repositório
# - Configure variáveis de ambiente
# - Deploy!
```

**🎉 Sua aplicação estará online em minutos!**