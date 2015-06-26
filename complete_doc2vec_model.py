from pymongo import MongoClient
import re
import cPickle as pickle
from gensim.models import Phrases, doc2vec, Doc2Vec
from nltk.tokenize.punkt import PunktSentenceTokenizer
import string

def build_doc2vec_model(save_file=False):
    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games']

    all_games = list(coll.find({'user_review': {"$exists": "true"},
                            'total_user_reviews': {'$ne': 0},
                            'game_name': {'$not': re.compile("Demo")} }))

    plv = PunktSentenceTokenizer()

    labeled_sentences = []
    for game in all_games:
        game_name = game['game_name']
        user_data = game['user_review']
        # critic_data = game['critic_review']

        user_reviews = user_data['reviews']

        for user_review in user_reviews:
            review = user_review['review']
            review = review.encode('ascii', 'replace')
            review = str(review).translate(string.maketrans("",""), string.punctuation)
            review_sentence = [sentence.split() for sentence in plv.tokenize(review.lower())]

            if len(review_sentence) == 0: 
                continue
            else:
                review_sentence = review_sentence[0]
            # else:
            #     sentences.extend(review_sentence)
            # game_label.append(game_name)

            sentence = doc2vec.LabeledSentence(words=review_sentence, labels=[game_name])
            labeled_sentences.append(sentence)

    model = Doc2Vec(alpha=0.025, min_alpha=0.025, workers=4) #, train_words=False, train_lbls=True)
    model.build_vocab(labeled_sentences)

    for epoch in range(10):
        model.train(labeled_sentences)
        model.alpha -= 0.002  # decrease the learning rate
        model.min_alpha = model.alpha  # fix the learning rate, no decay

    if save_file:
        with open('data/model.pkl', 'wb') as f_model:
            pickle.dump(model, f_model)
    else:
        return model

