from flask import Flask, request, render_template
import random
from pymongo import MongoClient
import cPickle as pickle
import shlex
from fuzzywuzzy import process as proc
from collections import defaultdict
import random

app = Flask(__name__)

def load_all_data():
    with open('../data/top_games.pkl', 'rb') as f_top:
        top_games = pickle.load(f_top)

    with open('../data/game_names.pkl', 'rb') as f_name:
        game_names = pickle.load(f_name)

    with open('../data/all_games.pkl', 'rb') as f_all:
        all_games = pickle.load(f_all)

    with open('../data/model.pkl', 'rb') as f_model:
        model = pickle.load(f_model)

    return top_games, game_names, all_games, model

def reformat_game_tags(game_tags):
    if len(game_tags) > 5:
        game_tags_5 = random.sample(game_tags, 5)
    else:
        game_tags_5 = game_tags

    return game_tags_5

def reformat_game_price(game_price):
    last_game_price = game_price.split('$')[-1]

    if 'Free to Play' in last_game_price:
        last_game_price = 'Free to Play'
    
    if 'Free' not in last_game_price:
        last_game_price = '$' + last_game_price

    return last_game_price

def get_game_data(game, all_games):
    game_df = all_games[all_games['meta_name'] == game]
    if len(game_df):
        # Change the game data to dictionary
        game_dict = game_df.to_dict()

        for index, value in game_dict.iteritems():
            game_dict[index] = value.values()[0]

        # Only select a random 5 game tags per game
        game_dict['game_tags'] = reformat_game_tags(game_dict['game_tags'])       
        # Change the format of the price
        game_dict['game_price'] = reformat_game_price(game_dict['game_price'])

        return game_dict

def load_predictions(user='all_users'):
    rec_games = top_games[user]
    # Get all the recommended games
    rec_game_names = game_names[rec_games]

    rec_games_data = []
    for game in rec_game_names:
        # Check if the metacritic game is in the steam games
        game_dict = get_game_data(game, all_games)
        if game_dict:
            rec_games_data.append(game_dict)
    return rec_games_data

@app.route('/')
def display():
    return render_template('index.html', DATA=PRED_DATA, TYPE=True)

@app.route('/user/<int:user_id>')
def display_user(user_id):
    return render_template('index.html', DATA=load_predictions(user_id))

@app.route('/search', methods=['GET', 'POST'])
def search():
    search_dict = defaultdict(list)
    if request.method == "POST":
        search_cond = request.form['search']
        all_condition = shlex.split(search_cond)
        for cond in all_condition:

            if cond[0] == '-':
                real_cond = proc.extractOne(cond[1:], vocab)
                search_dict['negative'].append(real_cond)
            else:
                real_cond = proc.extractOne(cond, vocab)
                search_dict['positive'].append(real_cond)

        result = model.most_similar(positive=search_dict['positive'], negative=search_dict['negative'], topn=100)
        games = [game[0] for game in result]

        rec_games_data = []
        for game in games:
            # Check if the metacritic game is in the steam games
            game_dict = get_game_data(game, all_games)
            if game_dict:
                rec_games_data.append(game_dict)

    return render_template('index.html', DATA=rec_games_data)
    # return str(games)


if __name__ == '__main__':
    top_games, game_names, all_games, model = load_all_data()
    vocab = model.vocab.keys()
    PRED_DATA = load_predictions()
    app.run(host='0.0.0.0', port=8080, debug=True)


