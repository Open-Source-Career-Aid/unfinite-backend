import langchain, os
from pdfChunks import extract_text_from_pdf_url
#from langchain.document_loaders import PDFMinerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

os.environ["OPENAI_API_KEY"] = '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'

url = input('url: ')

pdf = extract_text_from_pdf_url(url) #PDFMinerLoader(url)

text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size = 512,
    chunk_overlap  = 64,
    length_function = len,
)

pdf_chunks = text_splitter.create_documents([pdf])


# would store pdf_chunks in db here...

# would upload to index... 

query = input("query: ")

# would compute query vector and use it to search index (only for just uploaded doc)
from langchain.indexes import VectorstoreIndexCreator
index = VectorstoreIndexCreator().from_documents(pdf_chunks)
while True:
    print(index.query(query))
    query = input("query: ")