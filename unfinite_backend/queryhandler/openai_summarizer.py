import requests, html2text
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from readability import Document
from urllib.parse import urljoin
from langdetect import detect
import html
import re
import openai
import numpy as np
from time import time, sleep
from multiprocessing import Pool
import itertools
import openai, json
from django.http import JsonResponse
from django.conf import settings
from .models import *
from .scrape import attach_links, google_SERP, serphouse, scrapingrobot, scrapeitserp, bingapi

from .pool_funcs import f

from django.apps import apps
Query = apps.get_model('api', 'Query')
Relevantquestions = apps.get_model('api', 'Relevantquestions')
QuestionSummary = apps.get_model('api', 'QuestionSummary')

openai.api_key = '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'

def contentfinder(url, driver):

    # print('finding content for: ', url)

    ## should be set up in the main script
    # ==========
    # # Set up a headless Chrome browser instance with Selenium
    # chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # driver = webdriver.Chrome(driver, options=chrome_options)

    # Send a GET request to the URL and parse the HTML content with BeautifulSoup
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check if the page uses JavaScript
    try:
        if "javascript" in soup.find("html").get("class", []):
            # Use Selenium to load the JavaScript content and get the page source
            #driver = webdriver.Chrome()
            driver.get(url)
            html = driver.page_source
        else:
            html = requests.get(url).text
    except Exception:
        pass

    article = None
    t = soup.find('title')
    title = t.string if t is not None else None
    try:
        lang = detect(soup.body.get_text())
    except Exception:
        lang = None

    # Look for the <article>, <div>, or <section> tags that contain the main article content
    article = soup.find("article") or soup.find("div", class_="article") or soup.find("section", class_="article")

    # If the <article>, <div>, or <section> tags are not found, look for elements with specific CSS classes
    if not article:
        article = soup.find("div", class_="entry-content") or soup.find("div", class_="main-content")

    # If the <article>, <div>, or <section> tags are not found, look for the <main> tag
    if not article:
        article = soup.find("main")

    # If the <article>, <div>, <section>, or <main> tags are not found, use a content extraction library
    # if not article:
    #     doc = Document(response.text)
    #     article = BeautifulSoup(doc.summary(html_partial=True), "html.parser")
    
    driver.quit()

    # Returns the parsed article content
    return article, title, lang

def getpageobjects(listofurls, driver):
    data = {}
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    i = 0
    for url in listofurls:
        nextentry = ''
        article = contentfinder(url, driver)[0]
        if article is None: continue
        for element in article.find_all():
            # Check if the element is part of the readable article content and has a valid tag name
            if element.name in valid_tags:
                # Print the name of the element and its text content
                nextentry = nextentry + element.get_text(strip=True) + '\n'
                if len(nextentry)>2000:
                    if len(nextentry)>4000:
                        continue
                    data[i] = {'text':nextentry, 'url':url, 'vector': None}
                    i+=1
                    nextentry=''
                # print(element.name, ":", element.get_text(strip=True))

    #print('\n\n\n Got data from the urls! \n\n\n')

    return data

def getpageobjects_p(url, driver):

    data = []
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    nextentry = ''
    article = contentfinder(url, driver)[0]
    if article is None: return data
    for element in article.find_all():
        # Check if the element is part of the readable article content and has a valid tag name
        if element.name in valid_tags:
            # Print the name of the element and its text content
            nextentry = nextentry + element.get_text(strip=True) + '\n'
            if len(nextentry)>2000:
                if len(nextentry)>4000:
                    continue
                data.append({'text':nextentry, 'url':url})
                nextentry=''
            # print(element.name, ":", element.get_text(strip=True))

    #print('\n\n\n Got data from the urls! \n\n\n')

    return data

def generateembedding(chunkoftext, engine='text-embedding-ada-002'):
    #print(f"Generating embedding for {chunkoftext}!!!\n\n\n")
    response = openai.Embedding.create(input=chunkoftext,engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector

def cosinesimilarity(v1, v2):
    return np.dot(v1, v2)

def vectorsearch(query, vectordatabase, n=3):
    #print('\n\n\n VECTOR SEARCH!!! \n\n\n')
    vector = generateembedding(query)
    similarities = [(i, cosinesimilarity(vector, vectordatabase[i]['vector'])) for i in range(len(vectordatabase))]
    return sorted(similarities, key=lambda x: x[1])[0:n]

def gpt3_completion(prompt, engine='text-davinci-003', temp=0.6, top_p=1.0, tokens=2500, freq_pen=0.25, pres_pen=0.0):
    #print("Generating completion!")
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,)
            text = response['choices'][0]['text'].strip()
            text = re.sub('\s+', ' ', text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)

def summarizechunk(chunk, query, model):
    prompt = f'''Summarize the following text into a detailed paragraph to answer the given query:

    query: {query}

    text: {chunk}

    Summary:'''
    
    return gpt3_completion(prompt, engine=model)

def summarize(query, dictofchunks, model):

    text = f"""Summarise the following chunks of text of the form 'id: text' and provide citations of the form [id], e.g. [1], [2], etc. with respect to the given query.

    query: {query}

    """

    for key in dictofchunks:
        text = text + f"id: {key}, text:" + dictofchunks[key] + "\n"

    text = text + "Summary:"

    return gpt3_completion(text, engine=model)



def assign_vectors(data, engine='text-embedding-ada-002'):

    # id_text = [(k, v['text']) for k, v in data.items()]
    # text = list(map(lambda x: x[1], id_text))
    # response = openai.Embedding.create(input=text,engine=engine)
    # id_emb = [(id_text[d['index']][0], d['embedding']) for d in response['data']]
    text = [d['text'] for d in data]
    #text = list(map(lambda x: x[1], id_text))
    response = openai.Embedding.create(input=text,engine=engine)
    #id_emb = [(id_text[d['index']][0], d['embedding']) for d in response['data']]

    return response['data']

def summarizechunk_p(x, model):

    return summarizechunk(x[0], query=x[1], model=model)

def summary_generation_model(questionidx, topicidx, query, summarymodel='text-davinci-003', embeddingmodel='text-embedding-ada-002'):

    #chrome_options = Options() # faster to start the driver just once, not once per call to contentfinder...
    #chrome_options.add_argument('--headless')
    #driver = webdriver.Chrome('chromedriver', options=chrome_options)
    
    previoussummary = QuestionSummary.objects.filter(questionidx=questionidx, idx=topicidx, query=query)
    if len(previoussummary) == 1:
        return previoussummary[0].summary, previoussummary[0], True
    
    relevantquestions = Relevantquestions.objects.get(query=query, idx=topicidx)
    if len(relevantquestions.questions) == 0:
        raise Exception("No relevant questions found for this topic!")
    
    question = json.loads(relevantquestions.questions)[questionidx]

    summaryquery = f'{question}'

    searchurls = [x[0] for x in scrapingrobot(summaryquery)]
    #dictofdata = getpageobjects(searchurls, driver)
    with Pool(5) as p:
        dictofdata = list(itertools.chain.from_iterable(p.map(f, searchurls)))

    #print("pool done")

    embeddings = assign_vectors(dictofdata, engine=embeddingmodel)
    for embedding in embeddings:
        dictofdata[embedding['index']]['vector'] = embedding['embedding']

    sortedresults = vectorsearch(summaryquery, dictofdata)

    dictofchunks = {}

    for i in range(len(sortedresults)):
        
        dictofchunks[sortedresults[i][0]] = summarizechunk(dictofdata[sortedresults[i][0]]['text'], query=summaryquery, model=summarymodel)
        #print(dictofchunks[sortedresults[i][0]])

    finalsummary = summarize(summaryquery, dictofchunks, model=summarymodel)

    s = QuestionSummary(questionidx=questionidx, idx=topicidx, query=query, summary=finalsummary)
    s.save()

    return finalsummary, s, False