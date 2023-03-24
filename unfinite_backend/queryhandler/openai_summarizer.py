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
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from collections import defaultdict
from math import log10
from .pool_funcs import f, pooled_scrape
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

def contentfinder_noJS(url):

    print('finding content for: ', url)

    # Send a GET request to the URL and parse the HTML content with BeautifulSoup
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check if the page uses JavaScript
    try:
        if "javascript" in soup.find("html").get("class", []):
            pass
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

def getpagetext_inchunks(listofurls, driver):
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
                    return nextentry, listofurls.index(url)
                # print(element.name, ":", element.get_text(strip=True))

    #print('\n\n\n Got data from the urls! \n\n\n')
    return '', None

def getpagetext(url):
    text = ''
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    nextentry = ''
    article = contentfinder_noJS(url)[0]
    if article is None: return '', url
    for element in article.find_all():
        # Check if the element is part of the readable article content and has a valid tag name
        if element.name in valid_tags:
            # Print the name of the element and its text content
            text+=element.get_text(strip=True) + '\n'
            # print(element.name, ":", element.get_text(strip=True))
    print('\n\n\n Got data from the urls! \n\n\n')
    return (text, url)

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

def gpt3_completion(prompt, engine='text-davinci-003', temp=0.6, top_p=1.0, tokens=500, freq_pen=0.25, pres_pen=0.0):
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

def textrank(document, top_n=5):
    """
    Extracts the top n sentences from a document using the TextRank algorithm.
    
    Args:
        document (str): The text document to summarize.
        top_n (int): The number of sentences to extract (default: 5).
    
    Returns:
        summary (str): The summary of the document.
    """
    
    # Tokenize the document into sentences and words
    sentences = sent_tokenize(document)
    words = [word_tokenize(sentence.lower()) for sentence in sentences]
    
    # Remove stop words and punctuation
    stop_words = set(stopwords.words('english') + list(punctuation))
    filtered_words = [[word for word in sentence if word not in stop_words] for sentence in words]
    
    # Calculate word frequencies
    word_frequencies = defaultdict(lambda: 0)
    for sentence in filtered_words:
        for word in sentence:
            word_frequencies[word] += 1
    try:
        max_frequency = max(word_frequencies.values())
    except ValueError:
        max_frequency = 1
    for word in word_frequencies.keys():
        word_frequencies[word] /= max_frequency
    
    # Calculate sentence scores
    sentence_scores = defaultdict(lambda: 0)
    for i, sentence in enumerate(filtered_words):
        for word in sentence:
            sentence_scores[i] += word_frequencies[word]
        try:
            sentence_scores[i] /= len(sentence)
        except ZeroDivisionError:
            sentence_scores[i] = 0
    
    # Extract top n sentences
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_sentences = [(i, sentences[i]) for i, score in top_sentences]
    top_sentences_in_order_of_occurance = [x[1] for x in sorted(top_sentences, key=lambda x: x[0])]
    
    # Join the top sentences into a summary in order of appearance
    summary = ' '.join(top_sentences_in_order_of_occurance)
    return summary

def recursivesummariser(listofsummaries, howmanychunks, top_n=3):
    
    i = 0
    moresummaries = []
    chunk = ''
    while i<len(listofsummaries):
        if i%howmanychunks==0 and i!=0:
            moresummaries.append(textrank(chunk, howmanychunks))
            chunk=''
        chunk+=listofsummaries[i]+' '
        i+=1
    if len(chunk)!=0:
        moresummaries.append(textrank(chunk, howmanychunks))
    if sum([len(x.split(' ')) for x in moresummaries])>500:
        return recursivesummariser(moresummaries, howmanychunks, top_n)
    return moresummaries

def summarizewithextractive(text, top_n, howmanychunks):
    
    paragraphs = [x for x in text.split('\n') if len(x)!=0]
    
    summary = []
    for paragraph in paragraphs:
        summary.append(textrank(paragraph, top_n+2))
    
    summary = [x for x in summary if len(x.split('.'))>=3]
    
    finalsummary = '\n'.join(recursivesummariser(summary, howmanychunks, top_n))
    
    return finalsummary

def summarizechunk_p(x, model):

    return summarizechunk(x[0], query=x[1], model=model)

def summary_generation_model_old(questionidx, topicidx, query, summarymodel='text-davinci-003', embeddingmodel='text-embedding-ada-002'):

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

    searchurls = [x[0] for x in bingapi(summaryquery)]
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

def summary_generation_model(questionidx, topicidx, query, summarymodel='text-davinci-003', embeddingmodel='text-embedding-ada-002'):


    # chrome_options = Options() # faster to start the driver just once, not once per call to contentfinder...
    # chrome_options.add_argument('--headless')
    # driver = webdriver.Chrome('chromedriver', options=chrome_options)
    
    previoussummary = QuestionSummary.objects.filter(questionidx=questionidx, idx=topicidx, query=query)
    if len(previoussummary) == 1:
        return previoussummary[0].summary, previoussummary[0], True
    
    relevantquestions = Relevantquestions.objects.get(query=query, idx=topicidx)
    if len(relevantquestions.questions) == 0:
        raise Exception("No relevant questions found for this topic!")
    
    question = json.loads(relevantquestions.questions)[questionidx]

    summaryquery = f'{question}'

    searchurls = [x[0] for x in bingapi(summaryquery)]

    summaries = []
    relevanturls = []
    # for url in searchurls[0:5]:
    #     pagedata, url = getpagetext(url)
    #     if len(pagedata)>100: # random number, but if the text is too short, it's probably not useful
    #         summaries.append(summarizewithextractive(pagedata, 3, 4))
    #         relevanturls.append(url)
    with Pool(5) as p:
        tuples = p.map(pooled_scrape, searchurls[:5])

    summaries = list(itertools.chain.from_iterable(map(lambda x: x[0], tuples)))
    relevanturls = list(itertools.chain.from_iterable(map(lambda x: x[1], tuples)))

    prompt = """Please summarize the following texts, which are in the format text_id: text_content, into a concise and coherent answer to the question.
    
    """
    for i in range(len(summaries[:3])):
        prompt+=f'text_{i}: {summaries[i]}\n\n'

    prompt+=f'''Question: {summaryquery}
    
    Instructions: 1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 2. Don't add references at the end of the answer. 3. Structure the answer into multiple paragraphs where necessary. 4. Don't use additional numbers for citations apart from the provided text ids.
    
    Answer:'''

    finalsummary = gpt3_completion(prompt, engine=summarymodel)

    s = QuestionSummary(questionidx=questionidx, idx=topicidx, query=query, summary=finalsummary, urls=json.dumps(relevanturls[:3]))
    s.save()

    # driver.quit()

    return finalsummary, s, False

def summary_generation_model_gpt3_5_turbo(questionidx, topicidx, query, summarymodel='gpt-3.5-turbo'):

    # chrome_options = Options() # faster to start the driver just once, not once per call to contentfinder...
    # chrome_options.add_argument('--headless')
    # driver = webdriver.Chrome('chromedriver', options=chrome_options)
    
    previoussummary = QuestionSummary.objects.filter(questionidx=questionidx, idx=topicidx, query=query)
    if len(previoussummary) == 1:
        return previoussummary[0].summary, previoussummary[0], True
    
    relevantquestions = Relevantquestions.objects.get(query=query, idx=topicidx)
    if len(relevantquestions.questions) == 0:
        raise Exception("No relevant questions found for this topic!")
    
    question = json.loads(relevantquestions.questions)[questionidx]

    summaryquery = f'{question}'

    searchurls = [x[0] for x in bingapi(summaryquery)]

    summaries = []
    relevanturls = []
    # for url in searchurls[0:5]:
    #     pagedata, url = getpagetext(url)
    #     if len(pagedata)>100: # random number, but if the text is too short, it's probably not useful
    #         summaries.append(summarizewithextractive(pagedata, 3, 4))
    #         relevanturls.append(url)
    with Pool(5) as p:
        tuples = p.map(pooled_scrape, searchurls[:5])

    summaries = list(itertools.chain.from_iterable(map(lambda x: x[0], tuples)))
    relevanturls = list(itertools.chain.from_iterable(map(lambda x: x[1], tuples)))

    prompt = ""

    for i in range(len(summaries[:5])):
        prompt+=f'text {i}: {summaries[i]}\n\n'

    prompt+=f'''Question: {summaryquery}

    Answer:'''

    messages = [{
        "role": "user",
        "content": "You are an expert summarizer."
    },
    {
        "role": "user",
        "content": "Please summarize the following texts, which are in the format id: text_content, into a detailed and coherent answer to the question. 1-2 paragraphs are ideal."
    },
    {
        "role": "user",
        "content": """Instructions: 
1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
2. Don't add references at the end of the answer. 
3. Structure the answer into multiple paragraphs where necessary. 
4. For numbering a list, use the form 'li1', 'li2', and so on only."""
    },
    {
        "role": "user",
        "content": prompt
    }]

    temperature = 0.2
    max_length = 500
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0

    # making API request and error checking
    try:
        response = openai.ChatCompletion.create(
            model=summarymodel, 
            messages=messages, 
            temperature=temperature, 
            max_tokens=max_length, 
            top_p=top_p, 
            frequency_penalty=frequency_penalty, 
            presence_penalty=presence_penalty)
    except openai.error.RateLimitError as e:
        print("OpenAI API rate limit error! See below:")
        print(e)
        return None, None, None
    except Exception as e:
        print("Unknown OpenAI API error! See below:")
        print(e)
        return None, None, None

    # response = {}
    # response['choices'] = [{'text': "\n\nCancer diagnosis; Cancer staging; Cancer treatment options; Surgery; Radiation therapy; Chemotherapy; Targeted therapy; Immunotherapy; Hormone therapy; Clinical trials; Palliative care; Nutrition and exercise; Coping with cancer."}]
    # response['usage'] = {'total_tokens':69}
    
    finalsummary = response['choices'][0]['message']['content']
    # print(finalsummary)

    # finalsummary = gpt3_completion(prompt, engine=summarymodel)

    s = QuestionSummary(questionidx=questionidx, idx=topicidx, query=query, summary=finalsummary, urls=json.dumps(relevanturls[:3]))
    s.save()

    # driver.quit()

    return finalsummary, s, False