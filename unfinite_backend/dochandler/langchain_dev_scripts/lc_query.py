from pinecone_hybrid_search_retriever import PineconeHybridSearchRetriever
#from langchain.retrievers import PineconeHybridSearchRetriever
import pinecone, os
from langchain.embeddings import OpenAIEmbeddings
from pinecone_text.sparse import BM25Encoder

os.environ["OPENAI_API_KEY"] = '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'

bm25_encoder = BM25Encoder().default()
embeddings = OpenAIEmbeddings()
pinecone.init(api_key="1b0baa48-cedf-4397-b791-95d5e4f1ba76", environment="northamerica-northeast1-gcp")
index = pinecone.Index('unfinite-sparse-dense')

retriever = PineconeHybridSearchRetriever(embeddings=embeddings, sparse_encoder=bm25_encoder, index=index)
retriever.alpha = 0.7

to_query = input("\nquery: ")

result = retriever.get_relevant_documents(to_query, [10000])

print(result)