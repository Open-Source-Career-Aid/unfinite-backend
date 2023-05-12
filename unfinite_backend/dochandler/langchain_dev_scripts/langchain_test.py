import langchain, os, pinecone
from pdfChunks import extract_text_from_pdf_url
#from langchain.document_loaders import PDFMinerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from pinecone_hybrid_search_retriever import PineconeHybridSearchRetriever, RemoteSparseEncoder
from pinecone_text.sparse import BM25Encoder

os.environ["OPENAI_API_KEY"] = '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'
pinecone.init(api_key="1b0baa48-cedf-4397-b791-95d5e4f1ba76", environment="northamerica-northeast1-gcp")
index = pinecone.Index('unfinite-sparse-dense')

#bm25_encoder = BM25Encoder().default()
sparse = RemoteSparseEncoder('https://models.unfinite.co/job/', 'V_CSLlLynPYRYrqriL9Kncys23aQjLI2x728HP2P_DM')
embeddings = OpenAIEmbeddings()

url = input('url: ')

pdf = extract_text_from_pdf_url(url) #PDFMinerLoader(url)

# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size = 512,
#     chunk_overlap  = 64,
#     length_function = len,
# )
text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=128, chunk_overlap=16)

pdf_chunks = text_splitter.create_documents([pdf]) # replace with langchain's PDF->document loaders
print(pdf_chunks)
for_retriever = []
doc_id = 10000 # would need to make one in DB to get this...
for i, doc in enumerate(pdf_chunks):
    for_retriever.append((doc.page_content, {'metadata': {'document': doc_id, 'chunk': i, 'dev': True}}))

print(for_retriever)

# would store pdf_chunks in db here...
retriever = PineconeHybridSearchRetriever(embeddings=embeddings, sparse_encoder=sparse, index=index)
retriever.alpha = 0.7

# would upload to index... 
retriever.add_texts(for_retriever)

query = input("query: ")

# would compute query vector and use it to search index (only for just uploaded doc)
from langchain.indexes import VectorstoreIndexCreator
while True:
    print(retriever.get_relevant_documents(query, doc_ids=[doc_id]))
    query = input("query: ")