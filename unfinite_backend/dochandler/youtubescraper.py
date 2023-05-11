import json
from langchain.document_loaders import YoutubeLoader
# import the Document model from models
from .models import Document\

def scrape_youtube(url):
    loader = YoutubeLoader.from_youtube_url(url)
    content = loader.load()[0].page_content

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
    return chunks