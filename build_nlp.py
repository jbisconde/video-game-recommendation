import pandas as pd
from pymongo import MongoClient
import cPickle as pickle
from gensim.models import Word2Vec, Phrases, doc2vec, Doc2Vec
from nltk.tokenize.punkt import PunktSentenceTokenizer
from get_data import get_data_from_mongodb
import string

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

def calc_doc2vec():
    games_df = get_data_from_mongodb()
    games = get_games(games_df)
    sentences = get_reviews(games_df)

    labeled_sentences = []
    for i in xrange(len(games)):
        sentence = doc2vec.LabeledSentence(words=sentences[i], labels=[games[i]])
        labeled_sentences.append(sentence)

    model = Doc2Vec(alpha=0.025, min_alpha=0.025) #, train_words=False, train_lbls=True)
    model.build_vocab(labeled_sentences)

    for epoch in range(10):
        model.train(labeled_sentences)
        model.alpha -= 0.002  # decrease the learning rate
        model.min_alpha = model.alpha  # fix the learning rate, no decay

    return model

if __name__ == '__main__':
    model = calc_doc2vec()






