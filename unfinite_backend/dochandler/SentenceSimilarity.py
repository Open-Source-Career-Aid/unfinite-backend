from sentence_transformers import SentenceTransformer
import numpy as np
import time

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def similarity(v1, v2):  # return dot product of two vectors
    return np.dot(v1, v2)

def summarize_chunks(chunks):

    starttime = time.time()

    embeddings = model.encode(chunks)

    print(f'embedding took {time.time() - starttime} seconds')

    # get the top n chunks based on cosine similarity to the average chunk
    avg_embedding = np.mean(embeddings, axis=0)

    print(f'average embedding took {time.time() - starttime} seconds')

    # get the cosine similarity of each chunk to the average chunk
    similarities = [similarity(avg_embedding, embedding) for embedding in embeddings]

    print(f'cosine similarity took {time.time() - starttime} seconds')

    # get the top n chunks
    top_chunks = np.argsort(similarities)[-3:]

    print(f'argsort took {time.time() - starttime} seconds')

    # sort the top chunks
    top_chunks = sorted(top_chunks)

    print(f'sorting took {time.time() - starttime} seconds')

    # get the top chunks
    top_chunks = [chunks[i] for i in top_chunks]

    print(f'getting top chunks took {time.time() - starttime} seconds')

    # join the top chunks
    summarized_text = '\n'.join(top_chunks)

    print(f'joining chunks took {time.time() - starttime} seconds')

    # # breaking into sentences took a lot of time, so I commented it out

    # iverate over each chunk
    # for chunk in chunks:

        # # break each chunk into sentences
        # sentences = chunk.split('\n')

        # # get the embeddings for each sentence
        # embeddings = model.encode(sentences)

        # # get the top n sentences nased on cosine similarity to the average sentence
        # avg_embedding = np.mean(embeddings, axis=0)

        # # get the cosine similarity of each sentence to the average sentence
        # similarities = [similarity(avg_embedding, embedding) for embedding in embeddings]

        # # get the top n sentences
        # top_sentences = np.argsort(similarities)[-3:]

        # # sort the top sentences
        # top_sentences = sorted(top_sentences)

        # # get the top sentences
        # top_sentences = [sentences[i] for i in top_sentences]

        # # join the top sentences
        # summarized_chunk = '\n'.join(top_sentences)

        # # add the summarized chunk to the list of summarized chunks
        # listofsummarizedchunks.append(summarized_chunk)


    # # join the summarized chunks
    # summarized_text = '\n'.join(listofsummarizedchunks)

    return summarized_text