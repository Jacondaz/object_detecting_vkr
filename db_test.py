import requests
from bs4 import BeautifulSoup

def get_youtube_video_title(video_url):

    response = requests.get(video_url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page, status code: {response.status_code}")
    soup = BeautifulSoup(response.content, 'html.parser')
    title_tag = soup.find("title")
    
    if title_tag:
        title = title_tag.string
        title = title.replace(" - YouTube", "")
        return title
    else:
        raise Exception("Title tag not found")
    
video_url = 'https://www.youtube.com/watch?v=LhHm781jpqk'
title = get_youtube_video_title(video_url)
print(f"Название видео: {title}")