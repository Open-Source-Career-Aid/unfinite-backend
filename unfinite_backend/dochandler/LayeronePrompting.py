from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

options = ['The answer requires all the pages to be summarized', 'The answer is very specific']
def similarity(v1, v2):  # return dot product of two vectors
    return np.dot(v1, v2)

def get_modus_operandi(query):

    queryvector = model.encode(query)

    # load the vectors of the options
    optionvectors = model.encode(options)

    # calculate the similarity of the query with each option
    similarities = [similarity(queryvector, optionvector) for optionvector in optionvectors]

    # print all the options along with their similarity
    for option, similarity_ in zip(options, similarities):
        print(option, similarity_)

    # return the option with the highest similarity
    return options[np.argmax(similarities)]

# def vercor_search(query):

#     # get the modus operandi
#     modus_operandi = get_modus_operandi(query)

#     # based on the modus operandi, create a conditional
#     if modus_operandi == 'The answer requires all the pages to be summarized':
#         # search the query in the database
#         # return the result
#         pass
#     elif modus_operandi == 'The answer is very specific':
#         # search the query in the database
#         # return the result
#         pass

# if __name__ == '__main__':

#     while True:
#         query = input('Enter your query: ')
#         print(get_modus_operandi(query))