"""Taken from: https://github.com/hwchase17/langchain/blob/master/langchain/retrievers/pinecone_hybrid_search.py"""
import hashlib, requests
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Extra, root_validator
from langchain.embeddings.base import Embeddings
from langchain.schema import BaseRetriever, Document

class RemoteSparseEncoder():

    def __init__(self, endpoint, auth):
        self.endpoint = endpoint
        self.auth = auth

    def encode_documents(self, documents: List[str]) -> List[List[float]]:
        
        return requests.post(f"{self.endpoint}sparse_docs/", json={'texts': documents}, headers={'Authorization': self.auth}).json()['vectors']

    def encode_queries(self, queries: List[str]) -> List[List[float]]:
        
        return requests.post(f"{self.endpoint}sparse_qs/", json={'texts': queries}, headers={'Authorization': self.auth}).json()['vectors']


def hash_text(text: str) -> str:
    return str(hashlib.sha256(text.encode("utf-8")).hexdigest())

# Like the usual one, but contexts is a tuple with the second value being a metadata dictionary. 
def create_index(contexts: List[Tuple[str, Dict]], index: Any, embeddings: Any, sparse_encoder: Any, ids: Optional[List[str]] = None) -> None:
    batch_size = 128
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
        dense_embeds = embeddings.embed_documents([context[0] for context in context_batch])
        # create sparse vectors
        sparse_embeds = sparse_encoder.encode_documents([context[0] for context in context_batch])
        for s in sparse_embeds:
            s["values"] = [float(s1) for s1 in s["values"]]

        vectors = []
        # loop through the data and create dictionaries for upserts
        for doc_id, sparse, dense, metadata in zip(
            batch_ids, sparse_embeds, dense_embeds, meta
        ):
            if len(sparse["indices"]): # idk why this was really necessary
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


class PineconeHybridSearchRetriever(BaseRetriever, BaseModel):
    embeddings: Embeddings
    sparse_encoder: Any
    index: Any
    top_k: int = 5
    alpha: float = 0.5

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    def add_texts(self, texts: List[str], ids: Optional[List[str]] = None) -> None:
        create_index(texts, self.index, self.embeddings, self.sparse_encoder, ids=ids)

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        try:
            from pinecone_text.hybrid import hybrid_convex_scale  # noqa:F401
            from pinecone_text.sparse.base_sparse_encoder import (
                BaseSparseEncoder,  # noqa:F401
            )
        except ImportError:
            raise ValueError(
                "Could not import pinecone_text python package. "
                "Please install it with `pip install pinecone_text`."
            )
        return values

    def get_relevant_documents(self, query: str, doc_ids: List[int] = None) -> List[Document]:
        from pinecone_text.hybrid import hybrid_convex_scale

        sparse_vec = self.sparse_encoder.encode_queries(query)
        # convert the question into a dense vector
        dense_vec = self.embeddings.embed_query(query)
        # scale alpha with hybrid_scale
        dense_vec, sparse_vec = hybrid_convex_scale(dense_vec, sparse_vec, self.alpha)
        sparse_vec["values"] = [float(s1) for s1 in sparse_vec["values"]]
        # query pinecone with the query parameters
        f = {"dev": True}
        if doc_ids is not None:
            f.update({"document": {"$in": doc_ids}})

        if sparse_vec['indices']:
            result = self.index.query(
                vector=dense_vec,
                sparse_vector=sparse_vec,
                top_k=self.top_k,
                include_metadata=True,
                filter=f,
            )
        else:
            result = self.index.query(
                vector=dense_vec,
                top_k=self.top_k,
                include_metadata=True,
                filter=f,
            )
        final_result = []
        for res in result["matches"]:
            context = res['metadata'].pop('context')
            final_result.append(Document(page_content=context, metadata=res['metadata']))
        # return search results as json
        return final_result

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError