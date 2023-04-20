import pickle

# print the pickle file
with open('paraphrases.pkl', 'rb') as handle:
    b = pickle.load(handle)
    [print(i) for i in b]