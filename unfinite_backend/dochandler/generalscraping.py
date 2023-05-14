import requests, html2text
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from langdetect import detect

chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome('chromedriver', options=chrome_options)

def contentfinder(url, driver=driver):

    ## should be set up in the main script
    # ==========
    # # Set up a headless Chrome browser instance with Selenium
    # chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # driver = webdriver.Chrome('chromedriver', options=chrome_options)

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
    lang = detect(soup.body.get_text())

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

    # If the <article>, <div>, <section>, <main>, or content extraction library are not found, use the <body> tag
    if not article:
        article = soup.find("body")
    
    
    driver.quit()

    # Returns the parsed article content
    return article, title, lang

def find_title(url, driver=driver):
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

    t = soup.find('title')
    title = t.string if t is not None else None

    # Returns the parsed article content
    return title

def make_chunks_from_url(url, driver=driver):

    content, title, language = contentfinder(url, driver)

    content = content.get_text()
    
    # make words
    words = content.split(" ")

    # initialise chunks
    chunks = []

    # make chunks of words such that each chunk is less than 128
    chunk = []

    for word in words:
        if len(chunk) < 128:
            chunk.append(word)
        else:
            chunks.append(' '.join(chunk))
            chunk = [word]

    chunks.append(' '.join(chunk))

    # return chunks
    return chunks, title

# if __name__ == '__main__':
#     chrome_options = Options()
#     chrome_options.add_argument('--headless')
#     driver = webdriver.Chrome('chromedriver', options=chrome_options)
#     url = 'https://python.langchain.com/en/latest/modules/indexes/document_loaders/examples/url.html'
#     print(find_title(url, driver))
#     driver.quit()