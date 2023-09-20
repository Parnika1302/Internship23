from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func


app=FastAPI()
models.Base.metadata.create_all(bind=engine)

# class Marks(BaseModel):
#     sub1:float
#     sub2:float
#     sub3:float

class Marks(BaseModel):
    sub1: float
    sub1_grade: str
    sub2: float
    sub2_grade: str
    sub3: float
    sub3_grade: str

   

class Student(BaseModel):
    roll_no:int
    name:str
    age:int
    #marks :List[Marks]

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/student")
async def enter_student_data(student: Student, db:db_dependency):
    db_student= models.Student(
        roll_no= student.roll_no,
        name=student.name,
        age=student.age
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)


@app.post("/marks")
async def enter_student_marks(student_id:int, marks:Marks, db:db_dependency):
    db_student=db.query(models.Student).filter(models.Student.roll_no == student_id).first()

    if not db_student:
        raise HTTPException(status_code=404, detail="Student Not Found")

    db_marks=models.Marks(
        sub1=marks.sub1,
        sub2=marks.sub2,
        sub3=marks.sub3,
        student_id=db_student.roll_no
        )
    db.add(db_marks)
    db.commit()

# @app.delete("/delete/{student_id}")
# async def deleteStu(student_id:int, db:db_dependency):
#     find_student = db.query(models.Student).filter(models.Student.roll_no == student_id).first()
#     if(find_student is not None):
#         db.delete(find_student)
#         db.commit()    
#         return find_student
#     raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail= "Does not exist")


@app.get("/reportt")
async def get_report(db:db_dependency):
    #db = SessionLocal()
    
    # Calculate the highest overall score
    highest_score = db.query(models.Marks.student_id, func.sum(models.Marks.sub1 + models.Marks.sub2 + models.Marks.sub3).label("overall_score")).group_by(models.Marks.student_id).order_by(func.sum(models.Marks.sub1 + models.Marks.sub2 + models.Marks.sub3).desc()).first()
    students = db.query(models.Student).all()

    # Create a list to store the grades for each student and subject
    student_grades = []

    for student in students:
        # Retrieve the marks for the current student
        marks = db.query(models.Marks).filter(models.Marks.student_id == student.roll_no).first()

        if marks:
            # Calculate grades for each subject
            sub1_grade = calculate_grade(marks.sub1)
            sub2_grade = calculate_grade(marks.sub2)
            sub3_grade = calculate_grade(marks.sub3)

            # Create a dictionary to store the grades for the current student
            student_grade_data = {
                "student_id": student.roll_no,
                "name": student.name,
                "sub1_grade": sub1_grade,
                "sub2_grade": sub2_grade,
                "sub3_grade": sub3_grade,
            }

            student_grades.append(student_grade_data)

    if highest_score:
        student_id, overall_score = highest_score
        # Retrieve the student's details (name, etc.) if needed
        student = db.query(models.Student).filter(models.Student.roll_no == student_id).first()
        return {"student_id": student_id, "overall_score": overall_score, "student_name": student.name if student else None}, student_grades
    else:
        return {"message": "No data found"}


def calculate_grade(score):
    if score > 90:
        return 'A'
    elif 80 <= score <= 90:
        return 'B'
    elif 70 <= score < 80:
        return 'C'
    elif 50 <= score < 70:
        return 'D'
    else:
        return 'F'  # Fail or another suitable grade


# @app.get("/grades")
# async def get_student_grades(db: db_dependency):
#     # Retrieve all students and their marks from the database
#     students = db.query(models.Student).all()

#     # Create a list to store the grades for each student and subject
#     student_grades = []

#     for student in students:
#         # Retrieve the marks for the current student
#         marks = db.query(models.Marks).filter(models.Marks.student_id == student.roll_no).first()

#         if marks:
#             # Calculate grades for each subject
#             sub1_grade = calculate_grade(marks.sub1)
#             sub2_grade = calculate_grade(marks.sub2)
#             sub3_grade = calculate_grade(marks.sub3)

#             # Create a dictionary to store the grades for the current student
#             student_grade_data = {
#                 "student_id": student.roll_no,
#                 "name": student.name,
#                 "sub1_grade": sub1_grade,
#                 "sub2_grade": sub2_grade,
#                 "sub3_grade": sub3_grade,
#             }

#             student_grades.append(student_grade_data)

#     return student_grades
