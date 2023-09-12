from sqlalchemy import String, Integer, Column
from database import Base,engine

def create_tables():
    Base.metadata.create_all(engine)

class Student(Base):
    __tablename__ = 'student'

    roll_no = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    stream = Column(String(40), nullable=False)
