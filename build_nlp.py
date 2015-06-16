# Data Munging
import pandas as pd
from pymongo import MongoClient
import cPickle as pickle
from gensim.models import Word2Vec
from nltk.tokenize.punkt import PunktSentenceTokenizer

def get_data_from_mongodb():
    client = MongoClient()
    db = client.metacritic
    coll = db.reviews

    games_coll = list(coll.find())
    games_df = pd.DataFrame(games_coll)

    client.close()
    print 'There are %d reviews from MongoDB.' % len(games_df)
    return games_df

games_df = get_data_from_mongodb()

def get_reviews(games_df):
    plv = PunktSentenceTokenizer()
    reviews = games_df.excerpt.tolist()

    sentences = []
    for review in reviews:
        review_sentence = [sentence.split() for sentence in plv.tokenize(review.lower())]
        sentences.extend(review_sentence)

    return sentences

def pickle_word2vec(sentences, pickle=False):
    sentences = get_reviews(games_df)

    word2vec_model = Word2Vec(sentences, workers=4)

    if pickle:
        with open('data/word2vec_model.pkl', 'wb') as f:
            pickle.dump(word2vec_model, f)

def use_word2vec_model():
    with open('data/word2vec_model.pkl', 'rb') as f:
        model = pickle.load(f)