from ultralytics import YOLO
import os
from object_sort import object_sort
from pymongo import MongoClient


def detect(diction):
    i = 0
    fds = os.listdir(f'src/{diction}')
    for img in fds:
        model.predict(f'src/{diction}/' + img, save=True, save_txt=True, imgsz=640, conf=0.6)
        i += 1
        print(f'{i} изображение обработано')

if __name__ == '__main__':
    client = MongoClient("mongodb://localhost:27017/")
    db = client["video_base"]

    model = YOLO('yolov8n.pt')
    dictionary = os.listdir("src/")
    count = 0
    print("Проверка видео на обработанность...")
    for d in dictionary:
        if not db['already_processed'].find_one({"id": f'{d}'}):
            detect(d)
            object_sort(d)
            count += 1
            db['already_processed'].insert_one({"id": f'{d}'})
            print(f'{count} видео обработано')
    print("Все видео прошли проверку...")
