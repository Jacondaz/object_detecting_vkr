from typing import Union
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from pymongo import MongoClient

app = FastAPI()
client = MongoClient("mongodb://localhost:27017/")
db = client["video_base"]
templates = Jinja2Templates(directory="templates")

def convert_seconds_to_minutes(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

def create_video_player_url(url):
    pattern = "https://www.youtube.com/embed/"
    temp = url.split('?')[1]
    temp = temp.split('&')[0]
    temp = temp.split('=')[1]
    return pattern + temp

def find_common_times(time1, time2):
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

def and_search(alpha, list_with_collect):
    list_with_first_names = [coll["id"] for coll in db[alpha[0].lower()].find()]
    list_with_second_names = [coll["id"] for coll in db[alpha[1].lower()].find()]
    list_with_common = list(set(list_with_first_names) & set(list_with_second_names))
    if len(list_with_common) == 0:
        return False
    else:
        ans = list()
        for name_id in list_with_common:
            link = db['info_about_video'].find_one({"id": name_id})['link']
            name = db['info_about_video'].find_one({"id": name_id})['name']
            time1 = db[alpha[0].lower()].find_one({"id": name_id})["time"]
            time2 = db[alpha[1].lower()].find_one({"id": name_id})["time"]
            time_formatted1 = []
            time_formatted2 = []

            for entry in time1:
                if '-' in entry:
                    start, end = map(int, entry.split('-'))
                    start_formatted = convert_seconds_to_minutes(start)
                    end_formatted = convert_seconds_to_minutes(end)
                    time_formatted1.append(f"{start_formatted}-{end_formatted}")
                else:
                    time_formatted1.append(convert_seconds_to_minutes(int(entry)))
                
            for entry in time2:
                if '-' in entry:
                    start, end = map(int, entry.split('-'))
                    start_formatted = convert_seconds_to_minutes(start)
                    end_formatted = convert_seconds_to_minutes(end)
                    time_formatted2.append(f"{start_formatted}-{end_formatted}")
                else:
                    time_formatted2.append(convert_seconds_to_minutes(int(entry)))

            ans.append({"id": name_id, 
                        "name": name,
                        "link": link,
                        "class1": alpha[0], 
                        "class2": alpha[1],
                        "time1": time_formatted1,
                        "time2": time_formatted2
                        })
    return ans, "and"

def and_and_search(alpha, list_with_collect):
    ans = list()
    list_with_first_names = [coll["id"] for coll in db[alpha[0].lower()].find()]
    list_with_second_names = [coll["id"] for coll in db[alpha[1].lower()].find()]
    list_with_common = list(set(list_with_first_names) & set(list_with_second_names))
    if len(list_with_common) == 0:
        return False
    else:
        for name in list_with_common:
            t1 = db[alpha[0].lower()].find({'id': f'{name}'})
            t2 = db[alpha[1].lower()].find({'id': f'{name}'})
            times = find_common_times(t1[0]['time'], t2[0]['time'])
            name1 = alpha[0]
            name2 = alpha[1]
            if times:
                link = db['info_about_video'].find_one({"id": name})['link']
                name = db['info_about_video'].find_one({"id": name})['name']
                ans.append({"name": name, 
                            "link": link,
                            "time": times
                            })
            else:
                return False
    return ans, "and_and"

def or_search(alpha):
    ans = list()
    for alp in alpha:
        for coll in db[alp.lower()].find():
            link = db['info_about_video'].find_one({"id": coll["id"]})['link']
            name = db['info_about_video'].find_one({"id": coll["id"]})['name']
            temp_dict = {"class": alp}
            temp_dict["name"] = name
            temp_dict["link"] = link
            temp_dict["time"] = coll["time"]
            temp_dict["id"] = coll["id"]
            ans.append(temp_dict)
    return ans, "or"

def choose(expression: str):

    func = {
        '|': lambda x, y: or_search(x),
        '&': lambda x, y: and_search(x, y),
        '&&': lambda x, y: and_and_search(x, y)
    }

    alpha = list()
    symbol = list()

    list_with_collections = list(db.list_collection_names())
    list_with_collections.remove('already_processed')
    list_with_collections.remove('answer')
    list_with_collections.remove('info_about_video')

    temp_sym = expression[0]

    for i in range(1, len(expression)):
        if expression[i].isalpha():
            temp_sym += expression[i]
            if i == len(expression) - 1:
                alpha.append(temp_sym)
                temp_sym = ''
        else:
            if temp_sym != '':
                alpha.append(temp_sym)
            symbol.append(expression[i])
            temp_sym = ''

    if len(symbol) == 0 and len(alpha) == 1:
        try:
            ans = list()
            for coll in db[alpha[0].lower()].find():
                link = db['info_about_video'].find_one({"id": coll["id"]})['link']
                name = db['info_about_video'].find_one({"id": coll["id"]})['name']
                ans.append({"name": name, "link": link, "time": coll["time"], "id": coll["id"]})
            return ans, "single"
        except (ValueError, IndexError):
            return False
    elif len(alpha) == 0:
        return False
    elif len(alpha) == 2:
        if all(x.lower() in list_with_collections for x in alpha):
            if ('|' in symbol or '&' in symbol):
                return func[symbol[0]](alpha, list_with_collections)
            elif len(symbol) == 2:
                if symbol.count('&') == 2:
                    return func['&&'](alpha, list_with_collections)
            elif ' ' in symbol:
                return func['&&'](alpha, list_with_collections)
        else:
            return False
    elif len(alpha) == 3:
        if alpha[1].lower() == 'and' or alpha[1].lower() == 'or':
            temp = list()
            temp.append(alpha[0])
            temp.append(alpha[2])
            if alpha[1].lower() == 'and':
                return func['&'](temp, list_with_collections)
            else:
                return func['|'](temp, list_with_collections)
    else:
        return False


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post("/search", response_class=HTMLResponse)
def search_item(request: Request, name_cls: str = Form(...)):
    answer, type_ = choose(name_cls)
    db['answer'].insert_one({'answer':answer})
    if isinstance(answer, bool):
        return templates.TemplateResponse('result.html', {'request': request, "result": "Ошибка при поиске записей"})
    return templates.TemplateResponse('result.html', {'request': request, "result": answer, "type": type_})

@app.get("/search_video/{video_id}", response_class=HTMLResponse)
def link_item(request: Request, video_id: str):
    try:
        tags = list()
        link = db["info_about_video"].find({"id": video_id})[0]["link"]
        link = create_video_player_url(link)

        list_with_collections = list(db.list_collection_names())
        list_with_collections.remove('already_processed')
        list_with_collections.remove('answer')
        list_with_collections.remove('info_about_video')
        
        for class_ in list_with_collections:
            for video in db[class_].find():
                if video["id"] == video_id:
                    tags.append(class_)
                    break
        answer = [ans for ans in db['answer'].find()][-1]['answer']
        for element in answer:
            if element["id"] == video_id:
                if len(element) == 7:
                    return templates.TemplateResponse('video.html', {'request':request, 
                                                                     "link": link, 
                                                                     "tags": tags, 
                                                                     "time1": element['time1'],
                                                                     "time2": element["time2"],
                                                                     "type": 2})
                else:
                    time_entries = element["time"]
                    time_formatted = []
                    for entry in time_entries:
                        if '-' in entry:
                            start, end = map(int, entry.split('-'))
                            start_formatted = convert_seconds_to_minutes(start)
                            end_formatted = convert_seconds_to_minutes(end)
                            time_formatted.append(f"{start_formatted}-{end_formatted}")
                        else:
                            time_formatted.append(convert_seconds_to_minutes(int(entry)))
                break
        return templates.TemplateResponse('video.html', {'request':request, "link": link, "tags": tags, "time": time_formatted, "type":1})
    except Exception as e:
        return str(e)
    
@app.post("/search_single/{tag}", response_class=HTMLResponse)
def search_single(request: Request, tag: str):
    try:
        ans = list()
        for coll in db[tag.lower()].find():
            link = db['info_about_video'].find_one({"id": coll["id"]})['link']
            name = db['info_about_video'].find_one({"id": coll["id"]})['name']

            time_entries = coll["time"]
            time_formatted = []
            for entry in time_entries:
                if '-' in entry:
                    start, end = map(int, entry.split('-'))
                    start_formatted = convert_seconds_to_minutes(start)
                    end_formatted = convert_seconds_to_minutes(end)
                    time_formatted.append(f"{start_formatted}-{end_formatted}")
                else:
                    time_formatted.append(convert_seconds_to_minutes(int(entry)))

            ans.append({"name": name, "link": link, "time": time_formatted, "id": coll["id"]})
        return templates.TemplateResponse('result.html', {'request': request, "result": ans})
    except Exception as e:
        return str(e)