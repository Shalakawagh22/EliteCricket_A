from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["cricket_academy_db"]

users = db["users"]
admins = db["admin"]

print("MongoDB Connected")