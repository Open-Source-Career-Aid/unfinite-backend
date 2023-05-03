import langchain
from pdfChunks import pdftochunks_url

url = input('url: ')

chunks = pdftochunks_url(url)

