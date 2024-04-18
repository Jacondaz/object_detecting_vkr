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


def or_search(digits, list_with_collect):
    """
    for coll in db[list_with_collections[int(n)]].find():
    print(f'name: {coll["name"]}')
    print(f'time: {coll["time"]}\n')
    """
    for dig in digits:
        print(f'Видео с классом {list_with_collect[int(dig)]}: ')
        for coll in db[list_with_collect[int(dig)]].find():
            print(f'name: {coll["name"]}')
            print(f'time: {coll["time"]}\n')
        print("-------------------------------------")
    choose()


def and_search(digits, list_with_collect):
    """
    for coll in db[list_with_collections[int(n)]].find():
    print(f'name: {coll["name"]}')
    print(f'time: {coll["time"]}\n')
    """

    list_with_first_names = [coll["name"] for coll in db[list_with_collect[int(digits[0])]].find()]
    list_with_second_names = [coll["name"] for coll in db[list_with_collect[int(digits[1])]].find()]
    list_with_common = list(set(list_with_first_names) & set(list_with_second_names))
    if len(list_with_common) == 0:
        print("Нет общих видеороликов")
    else:
        for name in list_with_common:
            print(f'Видео {name}:')
            print(f'Класс: {list_with_collect[int(digits[0])]}')
            temp_elem = db[list_with_collect[int(digits[0])]].find({'name': f'{name}'})
            print(f'Время: {temp_elem[0]["time"]}')
            print(f'Класс: {list_with_collect[int(digits[1])]}')
            temp_elem = db[list_with_collect[int(digits[1])]].find({'name': f'{name}'})
            print(f'Время: {temp_elem[0]["time"]}')
            print("-------------------------------------")
    choose()


def and_and_search(digits, list_with_collect):
    list_with_first_names = [coll["name"] for coll in db[list_with_collect[int(digits[0])]].find()]
    list_with_second_names = [coll["name"] for coll in db[list_with_collect[int(digits[1])]].find()]
    list_with_common = list(set(list_with_first_names) & set(list_with_second_names))
    if len(list_with_common) == 0:
        print("Нет общих видеороликов")
    else:
        for name in list_with_common:
            t1 = db[list_with_collect[int(digits[0])]].find({'name': f'{name}'})
            t2 = db[list_with_collect[int(digits[1])]].find({'name': f'{name}'})
            times = find_common_times(t1[0]['time'], t2[0]['time'])
            name1 = list_with_collect[int(digits[0])]
            name2 = list_with_collect[int(digits[1])]
            print(f'Видео {name}:')
            print(f'Общее время для классов {name1} и {name2}: ')
            if times:
                print(times)
                print("-------------------------------------")
            else:
                print("Совпадений по времени не найдено")
                print("-------------------------------------")
    choose()


def find_common_times(time1, time2):
    print(time1)
    print(time2)
    comm_time = list()
    for i in time1:
        t1r = i.split('-')
        for j in time2:
            t2r = j.split('-')
            if len(t1r) != 1 and len(t2r) != 1:
                t1_range = list(range(int(t1r[0]), int(t1r[1]) + 1))
                t2_range = list(range(int(t2r[0]), int(t2r[1]) + 1))
                temp = list(set(t1_range) & set(t2_range))
                temp.sort()
                if temp:
                    comm_time.append(f'{temp[0]}-{temp[-1]}')
            else:
                if len(t1r) == 1 and len(t2r) == 1:
                    if t1r[0] == t2r[0]:
                        comm_time.append(t1r[0])
                elif len(t1r) == 1:
                    t2_range = list(range(int(t2r[0]), int(t2r[1]) + 1))
                    if int(t1r[0]) in t2_range:
                        comm_time.append(t1r[0])
                elif len(t2r) == 1:
                    t1_range = list(range(int(t1r[0]), int(t1r[1]) + 1))
                    if int(t2r[0]) in t1_range:
                        comm_time.append(t2r[0])
    return comm_time


def choose():
    func = {
        '|': lambda x, y: or_search(x, y),
        '&': lambda x, y: and_search(x, y),
        '&&': lambda x, y: and_and_search(x, y)
    }

    digits = list()
    symbol = list()

    list_with_collections = list(db.list_collection_names())
    list_with_collections.remove('already_processed')
    print("Доступные классы для выбора:")
    index_list = list()
    for index, cls in enumerate(list_with_collections):
        index_list.append(index)
        print(index, cls)

    print("Для выхода, введите exit/quit, или выберите номер класса")
    n = input("Выбор может быть одиночным или комбинацией 2 классов: ")
    print()

    temp_sym = n[0]

    # | - или
    # & - и

    if n == "exit" or n == "quit" or not temp_sym.isdigit():
        return

    for i in range(1, len(n)):
        if n[i].isdigit():
            temp_sym += n[i]
            if i == len(n) - 1:
                digits.append(temp_sym)
                temp_sym = ''
        elif n[i] == ' ':
            continue
        else:
            if temp_sym != '':
                digits.append(temp_sym)
            symbol.append(n[i])
            temp_sym = ''

    if len(symbol) == 0 and len(digits) == 1:
        try:
            for coll in db[list_with_collections[int(n)]].find():
                print(f'name: {coll["name"]}')
                print(f'time: {coll["time"]}\n')
            choose()
        except (ValueError, IndexError):
            print("Неверно выбран номер класса\n")
            choose()
    elif len(digits) == 0:
        print("Отсутствуют номера классов в запросе, попробуйте ещё раз\n")
        choose()
    elif len(digits) == 2:
        if all(int(x) in index_list for x in digits):
            if symbol[0] == '|' or symbol[0] == '&' and len(symbol) == 1:
                func[symbol[0]](digits, list_with_collections)
            elif len(symbol) == 2:
                if all(sym == '&' for sym in symbol):
                    func['&&'](digits, list_with_collections)
        else:
            print("Неверно выбраны номера классов\n")
            choose()
    else:
        print("Неверная команда\n")
        print(digits)
        choose()


if __name__ == '__main__':
    client = MongoClient("mongodb://localhost:27017/")
    db = client["video_base"]

    model = YOLO('yolov8n.pt')
    dictionary = os.listdir("src/")
    count = 0
    print("Проверка видео на обработанность...")
    for d in dictionary:
        if not db['already_processed'].find_one({"name": f'{d}'}):
            detect(d)
            object_sort(d)
            count += 1
            db['already_processed'].insert_one({"name": f'{d}'})
            print(f'{count} видео обработано')
    print("Все видео прошли проверку...")
    choose()
