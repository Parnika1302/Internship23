from sqlalchemy import Boolean, Column, ForeignKey, Integer, Float, String
from database import Base

class Student(Base):
    __tablename__ = 'student_info'
    roll_no = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False,index=True)
    age=Column(Integer,index=True)


class Marks(Base):
    __tablename__='marks'

    id = Column(Integer, primary_key=True, index=True)
    sub1= Column(Float, index=True)
    sub2= Column(Float, index=True)
    sub3= Column(Float, index=True)
    student_id=Column(Integer, ForeignKey("student_info.roll_no"))