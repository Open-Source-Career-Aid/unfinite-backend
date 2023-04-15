import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import csv
def research_topic():
    # Get the topic from the user
    cs_topic = ["https://arxiv.org/list/cs.AI/recent", "https://arxiv.org/list/cmp-lg/recent", "https://arxiv.org/list/stat.ML/recent"]
    for i in range(len(cs_topic)):
        r = requests.get(cs_topic[i])
        if r.status_code == 200:
            print("Success")
            soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup.prettify())
    return




