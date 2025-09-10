from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import engine, get_db
from models import Base
from routers import auth, accounts, transactions

load_dotenv()

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI(
    title="SaaS Controle Financeiro",
    description="Sistema de controle financeiro para pequenos negócios",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://yourdomain.com",  # Produção
    "https://*.vercel.app",  # Vercel domains
]

# Permitir origens dinâmicas em produção
if os.getenv("ENVIRONMENT") == "production":
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        origins.extend(allowed_origins_env.split(","))
    # Adicionar domínio do Vercel automaticamente
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        origins.append(f"https://{vercel_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)

# Rotas básicas
@app.get("/")
def read_root():
    return {"message": "SaaS Controle Financeiro API", "version": "1.0.0"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Testar conexão com banco
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# Handler global de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc)
        }
    )

# Export para Vercel
handler = app