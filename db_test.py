from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["video_base"]
coll = db["Pudge"]
dic = {
    "name": 1,
    "link": "https://www.youtube.com"
}
coll.insert_one(dic)