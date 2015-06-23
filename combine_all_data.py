import pandas as pd
import numpy as np
from collections import defaultdict
from pymongo import MongoClient
from fuzzywuzzy import process
from pymongo.errors import DuplicateKeyError
import cPickle as pickle

def steam_meta_join():

    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games2']

    steam_data = list(coll.find())
    steam = pd.DataFrame(steam_data)
    steam_games = steam.game_name.unique()

    coll2 = db['reviews']

    meta_data = list(coll2.find())
    meta = pd.DataFrame(meta_data)
    meta_games = meta.game_name.unique()

    meta_steam_games = defaultdict(str)
    for meta_game in meta_games:

        steam_game = process.extractOne(meta_game, steam_games)
        if steam_game[1] >= 90:
            meta_steam_games[meta_game] = steam_game[0]
        else:
            meta_steam_games[meta_game] = ''

        print meta_game
        print steam_game

    client.close()

def input_to_mongodb(games):
    client = MongoClient()
    db = client['metacritic']
    coll = db['all_games']
    steam_coll = db['steam_games2']

    for meta_game, steam_game in games.iteritems():
        if steam_game:
            try:
                game_dict = steam_coll.find({'game_name': steam_game}).next()
                game_dict['meta_name'] = meta_game
                game_dict['game_link'] = game_dict['game_link'].split('?')[0]

                coll.insert(game_dict, continue_on_error=True)
                print meta_game
                print steam_game
            except DuplicateKeyError:
                print meta_game

    client.close()

def apply_agg_func(meta_grouper):
    total_reviews = meta_grouper['excerpt'].count()
    avg_score = np.round(meta_grouper['score'].mean() / 20., 2)
    return pd.Series([total_reviews, avg_score], index=['total_reviews', 'avg_score'])


def get_meta_data_to_mongodb():
    client = MongoClient()
    db = client['metacritic']
    coll = db['all_games']
    meta_coll = db['reviews']
    
    all_games = list(coll.find())
    meta_games = list(meta_coll.find())

    meta_df = pd.DataFrame(meta_games)
    meta_df.loc[:, 'score'] = meta_df.loc[:, 'score'].astype(float)
    meta_grouper = meta_df.groupby('game_name')

    meta_summary = meta_grouper.apply(apply_agg_func)

    for game in all_games:
        meta_name = game['meta_name']
        agg_values = meta_summary.ix[meta_name]
        game['total_reviews'] = agg_values['total_reviews']
        game['avg_score'] = agg_values['avg_score']

        coll.update({'meta_name':meta_name}, {"$set": game}, upsert=False)

    client.close()

def write_all_games_to_file():
    client = MongoClient()
    db = client['metacritic']
    coll = db['all_games']

    # coll_games = list(coll.find())
    # all_games = defaultdict(dict)

    # for game in coll_games:
    #     game_id = game['meta_name']
    #     all_games[game_id] = game
    all_games = pd.DataFrame(list(coll.find()))

    with open('data/all_games.pkl', 'wb') as f:
        pickle.dump(all_games, f)

    client.close()





