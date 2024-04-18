from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["video_base"]
collect = db["Pudge"]
dic ={
    "name": "1",
    "time": "1-18"
}
collect.insert_one(dic)