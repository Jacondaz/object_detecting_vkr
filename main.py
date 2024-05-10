from typing import Union
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
#import youtube_dl

app = FastAPI()
client = MongoClient("mongodb://localhost:27017/")
db = client["video_base"]
templates = Jinja2Templates(directory="templates")

# def get_video_title(video_url):
#     ydl_opts = {'quiet': True, 'extract_flat': True}
#     with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(video_url, download=False)
#         return info.get('title', None)
    
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
    #заменить name на id
    #доделать логику
    list_with_first_names = [coll["name"] for coll in db[alpha[0].lower()].find()]
    list_with_second_names = [coll["name"] for coll in db[alpha[1].lower()].find()]
    list_with_common = list(set(list_with_first_names) & set(list_with_second_names))
    if len(list_with_common) == 0:
        return False
    else:
        ans = list()
        for name in list_with_common:
            temp_elem = db[alpha[0].lower()].find({'name': f'{name}'})
            temp_elem2 = db[alpha[1].lower()].find({'name': f'{name}'})
            ans.append({"Name": name, 
                        "Class1": alpha[0], 
                        "Class2": alpha[1],
                        })
    return ans

def and_and_search(alpha, list_with_collect):
    ans = list()
    list_with_first_names = [coll["name"] for coll in db[alpha[0].lower()].find()]
    list_with_second_names = [coll["name"] for coll in db[alpha[1].lower()].find()]
    list_with_common = list(set(list_with_first_names) & set(list_with_second_names))
    if len(list_with_common) == 0:
        return False
    else:
        for name in list_with_common:
            t1 = db[alpha[0].lower()].find({'name': f'{name}'})
            t2 = db[alpha[1].lower()].find({'name': f'{name}'})
            times = find_common_times(t1[0]['time'], t2[0]['time'])
            name1 = alpha[0]
            name2 = alpha[1]
            if times:
                ans.append({"name": name, 
                            "Link":  "some_link",
                            "time": times
                            })
            else:
                return False
    return ans

def or_search(alpha, list_with_collect):
    ans = list()
    for alp in alpha:
        temp_dict = {"class": alp}
        for coll in db[alp].find():
            #name = get_video_title(coll["link"])
            temp_dict["name"] = coll["name"]
            temp_dict["link"] = coll["link"]
            temp_dict["time"] = coll["time"]
            temp_dict["id"] = coll["id"]
        ans.append(temp_dict)
    return ans

def choose(expression: str):

    func = {
        '|': lambda x, y: or_search(x, y),
        '&': lambda x, y: and_search(x, y),
        '&&': lambda x, y: and_and_search(x, y)
    }

    alpha = list()
    symbol = list()

    list_with_collections = list(db.list_collection_names())
    #list_with_collections.remove('already_processed')
    list_with_collections = [x.lower() for x in list_with_collections]

    temp_sym = expression[0]

    # | - или
    # & - и

    for i in range(1, len(expression)):
        if expression[i].isalpha():
            temp_sym += expression[i]
            if i == len(expression) - 1:
                alpha.append(temp_sym)
                temp_sym = ''
        elif expression[i] == ' ':
            continue
        else:
            if temp_sym != '':
                alpha.append(temp_sym)
            symbol.append(expression[i])
            temp_sym = ''

    if len(symbol) == 0 and len(alpha) == 1:
        try:
            ans = list()
            for coll in db[alpha[0]].find():
                #name = get_video_title(coll["link"])
                ans.append({"name": coll["name"], "link": coll["link"], "time": coll["time"], "id": coll["id"]})
            return ans, alpha
        except (ValueError, IndexError):
            return False
    elif len(alpha) == 0:
        return False
    elif len(alpha) == 2:
        if all(x.lower() in list_with_collections for x in alpha):
            if symbol[0] == '|' or symbol[0] == '&' and len(symbol) == 1:
                return func[symbol[0]](alpha, list_with_collections), alpha
            elif len(symbol) == 2:
                if all(sym == '&' for sym in symbol):
                    return func['&&'](alpha, list_with_collections), alpha
        else:
            return False
    else:
        return False


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post("/search", response_class=HTMLResponse)
def search_item(request: Request, name_cls: str = Form(...)):
    answer, classes = choose(name_cls)
    if isinstance(answer, bool):
        return templates.TemplateResponse('result.html', {'request': request, "result": "Ошибка при поиске записей"})
    return templates.TemplateResponse('result.html', {'request': request, "result": answer})

@app.get("/search_video/{video_id}", response_class=HTMLResponse)
def link_item(request: Request, video_id: str):
    try:
        #доделать дополнительные теги под видео
        tags = list()
        link = db["info_about_video"].find({"id": video_id})[0]["link"]
        list_with_collections = list(db.list_collection_names())
        for class_ in list_with_collections:
            for video in db[class_].find():
                if video["id"] == video_id:
                    tags.append(class_)
                    break
        return templates.TemplateResponse('video.html', {'request':request, "link": link, "tags": tags})
    except Exception as e:
        return str(e)
    
@app.post("/search_single/{tag}", response_class=HTMLResponse)
def search_single(request: Request, tag: str):
    try:
        ans = list()
        for coll in db[tag].find():
            #name = get_video_title(coll["link"])
            ans.append({"name": coll["name"], "link": coll["link"], "time": coll["time"], "id": coll["id"]})
        return templates.TemplateResponse('result.html', {'request': request, "result": ans})
    except Exception as e:
        return str(e)