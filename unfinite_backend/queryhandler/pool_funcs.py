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
import openai, json
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from collections import defaultdict
from math import log10

# DJANGO MUST NOT BE IMPORTED IN THIS FILE!!! it will be broken by the pooling that happens here...

chrome_options = Options() # faster to start the driver just once, not once per call to contentfinder...
chrome_options.add_argument('--headless')
driver = webdriver.Chrome('chromedriver', options=chrome_options)
def contentfinder(url):#, driver):

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

def getpageobjects_p(url):

    data = []
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    nextentry = ''
    article = contentfinder(url)[0]
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

def getpagetext_p(url):
    # Define a list of valid tag names
    valid_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
    i = 0
    for url in listofurls:
        nextentry = ''
        article = contentfinder(url)[0]
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
    if sum([len(x.split(' ')) for x in moresummaries])>2000:
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

def contentfinder_noJS(url):

    #print('finding content for: ', url)

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
    #print('\n\n\n Got data from the urls! \n\n\n')
    return (text, url)

def pooled_scrape(url):

    pagedata, url = getpagetext(url)
    summaries = []
    relevanturls = []

    if len(pagedata)>100: # random number, but if the text is too short, it's probably not useful
        summaries.append(summarizewithextractive(pagedata, 3, 4))
        relevanturls.append(url)
    
    return (summaries, relevanturls)


def f(x): 
    o = getpageobjects_p(x)
    driver.close()
    return o

