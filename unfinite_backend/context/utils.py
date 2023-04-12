from typing import List, Tuple
from django.http import JsonResponse
from gensim.models.ldamodel import LdaModel
from gensim.corpora.dictionary import Dictionary
from nltk.tokenize import word_tokenize
import numpy as np


def preprocess(text: str) -> List[str]:
    """Tokenize and preprocess the text"""
    tokens = word_tokenize(text.lower())
    return [token for token in tokens if token.isalpha()]


def get_topics(text: str, num_topics: int = 5) -> List[Tuple[str, float]]:
    """Extract topics from the text using LDA"""
    dictionary = Dictionary.load('context/dictionary.dict')
    lda_model = LdaModel.load('context/model.lda')
    bow_vector = dictionary.doc2bow(preprocess(text))
    topic_weights = lda_model[bow_vector]
    return [(lda_model.print_topic(topic[0]), np.round(topic[1], 3)) for topic in topic_weights]


def highlight_topics(text: str, num_topics: int = 5) -> str:
    """Highlight the topics in the text"""
    topics = get_topics(text, num_topics)
    for topic in topics:
        text = text.replace(topic[0].split('*')[1], f'<mark>{topic[0].split("*")[1]}</mark>')
    return text


def get_topics_view(request, *args, **kwargs):
    text = request.POST.get('text')
    num_topics = request.POST.get('num_topics', 5)
    topics = get_topics(text, int(num_topics))
    return JsonResponse({'topics': topics})