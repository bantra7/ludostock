from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from environs import Env

env = Env()
env.read_env(env.str('ENV_PATH', '.env'))

SQLALCHEMY_DATABASE_URL = env.str("DATABASE_URL", "duckdb:////mnt/data/ludostock.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db(sql_path: str):
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.connect() as conn:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
                conn.commit()