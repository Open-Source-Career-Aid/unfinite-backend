from typing import List, Tuple
from gensim.models.ldamodel import LdaModel
from gensim.corpora.dictionary import Dictionary
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import numpy as np
from gensim.utils import simple_preprocess
from nltk.stem import WordNetLemmatizer


def preprocess(text: str) -> str:
    """Tokenize and preprocess the text"""
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [w for w in tokens if w not in stop_words]
    lem = WordNetLemmatizer()
    lemma_words = [lem.lemmatize(w) for w in words]
    custom_token = " ".join([token for token in lemma_words if token.isalpha()])
    return simple_preprocess(custom_token)


def get_topics(cleaned_text: str, num_topics: int = 5) -> List[Tuple[str, float]]:
    """Extract topics from the text using LDA"""
    tokenized_texts = [text.split() for text in cleaned_text]
    # Create dictionary
    dictionary = Dictionary(tokenized_texts)
    corpus = [dictionary.doc2bow(tokens) for tokens in tokenized_texts]
    # Train LDA model
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=5, passes=10)
    bow_vector = dictionary.doc2bow(cleaned_text.split())
    topic_weights = lda_model[bow_vector]
    return [(lda_model.print_topic(topic[0]), np.round(topic[1], 3)) for topic in topic_weights]


def highlight_topics(text: str, num_topics: int = 5) -> str:
    """Highlight the topics in the text"""
    topics = get_topics(text, num_topics)
    for topic in topics:
        text = text.replace(topic[0].split('*')[1], f'<mark>{topic[0].split("*")[1]}</mark>')
    return text


def extract_topics_from_list(texts: List[str], num_topics: int = 5) -> List[List[Tuple[str, float]]]:
    """Extract topics from a list of texts" with generators"""
    try:
        if not isinstance(texts, list):
            raise TypeError("texts must be a list")
        for text in texts:
            text = preprocess(text)
            yield highlight_topics(text, num_topics)
    except (TypeError, StopIteration) as e:
        print(e)
        return None
