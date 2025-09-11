from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do banco de dados para Vercel/Neon
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback para desenvolvimento local com SQLite
    DATABASE_URL = "sqlite:///./saas_financeiro.db"

# Configurações otimizadas
engine_config = {
    "echo": os.getenv("DEBUG") == "true"
}

# Para PostgreSQL/Neon, adicionar configurações específicas
if DATABASE_URL.startswith("postgresql"):
    engine_config.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300
    })
    
    # Para Neon, adicionar configurações SSL
    if "neon.tech" in DATABASE_URL or os.getenv("ENVIRONMENT") == "production":
        engine_config["connect_args"] = {"sslmode": "require"}

# Para SQLite, adicionar configurações específicas
if DATABASE_URL.startswith("sqlite"):
    engine_config["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_config)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()