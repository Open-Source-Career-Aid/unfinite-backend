from django.core.management.base import BaseCommand, CommandError
import pinecone, pickle, hashlib, json
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dochandler.models import Document
from pinecone_text.sparse import BM25Encoder
from tqdm import tqdm

# stuff this is from langchain source
def hash_text(text: str) -> str:
    return str(hashlib.sha256(text.encode("utf-8")).hexdigest())

# I modified this one for populating the new index
def create_index(contexts: Tuple[List[str], Dict], index: Any, embeddings: Embeddings, sparse_encoder: Any, ids: Optional[List[str]] = None) -> None:
    batch_size = 32
    _iterator = range(0, len(contexts), batch_size)
    try:
        from tqdm.auto import tqdm

        _iterator = tqdm(_iterator)
    except ImportError:
        pass

    if ids is None:
        # create unique ids using hash of the text
        ids = [hash_text(context[0]) for context in contexts]

    for i in _iterator:
        # find end of batch
        i_end = min(i + batch_size, len(contexts))
        # extract batch
        context_batch = contexts[i:i_end]
        batch_ids = ids[i:i_end]
        # add context passages as metadata
        meta = [{"context": context[0], "chunk": context[1]["metadata"]["chunk"], 
                 "document": context[1]["metadata"]["document"], "dev": context[1]["metadata"]["dev"]} for context in context_batch]
        # create dense vectors
        dense_embeds = embeddings.embed_documents(context_batch)
        # create sparse vectors
        sparse_embeds = sparse_encoder.encode_documents([context[0] for context in context_batch)
        for s in sparse_embeds:
            s["values"] = [float(s1) for s1 in s["values"]]

        vectors = []
        # loop through the data and create dictionaries for upserts
        for doc_id, sparse, dense, metadata in zip(
            batch_ids, sparse_embeds, dense_embeds, meta
        ):
            vectors.append(
                {
                    "id": doc_id,
                    "sparse_values": sparse,
                    "values": dense,
                    "metadata": metadata,
                }
            )

        # upload the documents to the new hybrid index
        index.upsert(vectors)

class ExistingDenseGetter():

    def __init__(self, vectors, id_to_idx):

        self.vectors = vectors
        self.map = id_to_idx

    def embed_documents(context_batch):

        return [list(self.vectors[self.map[entry[1]['id']]]) for entry in context_batch]

class Command(BaseCommand):
    def handle(self, **options):
        metadata = pickle.load(open('metadata.pickle', 'rb'))
        vectors = np.load('vectors.npy')

        print("Mapping...")
        id_to_idx = {}
        for i in range(len(metadata)):
            id_to_idx[metadata[i]['id']] = i
        
        embeddings = ExistingDenseGetter(vectors, id_to_idx)

        tuples = []
        doc_chunks = {}

        print("Getting chunks...")
        for i in tqdm(range(len(metadata))):
            doc_id = metadata[i]['metadata']['document']
            if doc_id not in doc_chunks:
                chunks = json.loads(Document.objects.get(id=doc_id).chunks)
                doc_chunks[doc_id] = chunks
            
            tuples.append((doc_chunks[doc_id][metadata[i]['metadata']['chunk']], metadata[i]))

        print("Connecting to index...")
        pinecone.init(api_key="1b0baa48-cedf-4397-b791-95d5e4f1ba76", environment="northamerica-northeast1-gcp")
        index = pinecone.Index('unfinite-sparse-dense')

        bm25_encoder = BM25Encoder().default()
        print("Upserting batches...")
        #create_index(tuples, index, embeddings, bm25_encoder)




