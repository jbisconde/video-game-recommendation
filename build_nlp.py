# Data Munging
import pandas as pd
from pymongo import MongoClient
import cPickle as pickle
from gensim.models import Word2Vec, Phrases
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
        sentences.extend(review_sentence)

    return sentences

# not used
def tokenize(doc):
    plv = PunktLanguageVars()
    snowball = SnowballStemmer('english')
    return [snowball.stem(word) for word in plv.word_tokenize(doc.lower())]

# not used
def calc_tfidf(content):

    vectorizer = TfidfVectorizer('content', tokenizer=tokenize,
                                 stop_words=stopwords.words('english'),
                               strip_accents='unicode',norm='l2')
    tfidf = vectorizer.fit_transform(content)
    return tfidf.toarray()

# not used
def get_summarization(documents):
    for article in documents:
        article_sentences = find_sentence(article)
        tfidf = calc_tfidf(article_sentences)
        max_index = tfidf.mean(axis=1).argmax()
        summarization = article_sentences[max_index]
        print summarization, '\n'

def replace_pronouns(games_df):
    total_reviews = len(games_df)
    for i in xrange(total_reviews):
        game = games_df.loc[i, 'game_name']
        game = game.replace('-', ' ').strip()

    return games_df

def pickle_word2vec(sentences, save_pickle=False):
    sentences = get_reviews(games_df)

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


if __name__ == '__main__':
    games_df = get_data_from_mongodb()
    games = replace_pronouns(games_df)
    sentences = get_reviews(games)
    pickle_word2vec(sentences, True)

