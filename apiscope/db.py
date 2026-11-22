"""Optional SQLAlchemy persistence; database support activates when DATABASE_URL is set."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
DATABASE_URL=os.getenv("DATABASE_URL","")
engine=create_engine(DATABASE_URL,pool_pre_ping=True) if DATABASE_URL else None
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False) if engine else None
class Base(DeclarativeBase): pass
