from fastapi import APIRouter
from models import Student
from db import collection_name
from schema import list_serial
from bson import ObjectId

router = APIRouter()

@router.get("/")
async def get_data():
    data = list_serial(collection_name.find())
    return data


@router.post("/")
async def post_data(data:Student):
    collection_name.insert_one(dict(data))

@router.put("/{id}")
async def put_data(id:str, data: Student):
    collection_name.find_one_and_update({"_id": ObjectId(id)},{"$set":dict(data)})

@router.delete("/{id}")
async def delete(id:str):
    collection_name.find_one_and_delete({"_id":ObjectId(id)})

   