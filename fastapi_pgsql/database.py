from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:Parnika%401302@localhost/Student")

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
