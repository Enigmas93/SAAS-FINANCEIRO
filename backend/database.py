from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do banco de dados para Vercel/Neon
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback para desenvolvimento local
    DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/saas_financeiro"

# Configurações otimizadas para Vercel/Neon
engine_config = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": os.getenv("DEBUG") == "true"
}

# Para Neon, adicionar configurações SSL
if "neon.tech" in DATABASE_URL or os.getenv("ENVIRONMENT") == "production":
    engine_config["connect_args"] = {"sslmode": "require"}

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