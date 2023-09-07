from pymongo import MongoClient

connection_string = f"mongodb+srv://parnika1302:Parnika%401302@pythonmongo.ozetbjv.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)

db=client.todo_db
collection_name = db["todo_collection"]

