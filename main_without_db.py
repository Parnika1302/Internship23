from fastapi import FastAPI
from pydantic import BaseModel

app= FastAPI()

db={}

class Student(BaseModel):
    name:str
    stream:str

@app.post("/")
async def create(student: Student):
    db[student.name] = student.stream
    return{"Student": student}

@app.get("/")
async def get_all_data():
    return db

@app.delete("/")
def delete(name:str):
    del db[name]
    return db

@app.put("/")
def update_data(student:Student):
    db[student.name]=student.stream
    return db



