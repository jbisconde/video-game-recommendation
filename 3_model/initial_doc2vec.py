import pandas as pd
from pymongo import MongoClient
import cPickle as pickle
from gensim.models import Word2Vec, Phrases, doc2vec, Doc2Vec
from nltk.tokenize.punkt import PunktSentenceTokenizer
from get_data import get_data_from_mongodb
import string


def get_reviews(games_df):
    plv = PunktSentenceTokenizer()
    reviews = games_df.excerpt.tolist()

    sentences = []
    for review in reviews:
        review = review.encode('ascii', 'replace')
        review = str(review).translate(string.maketrans("",""), string.punctuation)
        review_sentence = [sentence.split() for sentence in plv.tokenize(review.lower())]
        if len(review_sentence) == 0: 
            sentences.append([])
        else:
            sentences.extend(review_sentence)

    return sentences

def get_games(games_df):
    games = games_df.game_name.tolist()
    for i, game in enumerate(games):
        games[i] = 'GAME_' + '_'.join(game.replace('-', ' ').split())

    return games

def pickle_word2vec(sentences, save_pickle=False):
    # model = Word2Vec(sentences, size=100, window=5, min_count=5, workers=4)
    word2vec_model = Word2Vec(sentences, workers=4)

    if save_pickle:
        with open('data/word2vec_model.pkl', 'wb') as f:
            pickle.dump(word2vec_model, f)

def top_n_similar_words(sentences, base_word, n):
    bigram_transformer = Phrases(sentences)
    bi_sentences = bigram_transformer[sentences]
    model = Word2Vec(trigram_transformer[sentences], workers=4)

    similar_words = model.most_similar(base_word, topn=n)

    return similar_words

def use_word2vec_model():
    with open('data/word2vec_model.pkl', 'rb') as f:
        model = pickle.load(f)

def get_tags():
    with open('data/all_games.pkl', 'rb') as f_all:
        all_games = pickle.load(f_all)
    game_tags = all_games[ ['meta_name', 'game_tags'] ].set_index('meta_name')
    game_tags_dict = game_tags['game_tags'].to_dict()

    return game_tags_dict


def calc_doc2vec(game_tags_dict):
    games_df = get_data_from_mongodb()
    # games = get_games(games_df)
    games = games_df.game_name.tolist()
    sentences = get_reviews(games_df)
    # game_tags_dict = get_tags()

    labeled_sentences = []
    for i in xrange(len(games)):
        game_labels = [games[i]]
        # tag_labels = game_tags_dict.get(games[i], [])
        # game_labels.extend(tag_labels)
        sentence = doc2vec.LabeledSentence(words=sentences[i], labels=game_labels)
        labeled_sentences.append(sentence)

    model = Doc2Vec(alpha=0.025, min_alpha=0.025) #, train_words=False, train_lbls=True)
    model.build_vocab(labeled_sentences)

    for epoch in range(10):
        model.train(labeled_sentences)
        model.alpha -= 0.002  # decrease the learning rate
        model.min_alpha = model.alpha  # fix the learning rate, no decay

    return model

def save_model(model):
    with open('data/model.pkl', 'wb') as f_model:
        pickle.dump(model, f_model)







