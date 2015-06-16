import pandas as pd
from get_data import get_data_from_mongodb


games_df = get_data_from_mongodb()
ratings = games_df[ ['critic', 'game_name', 'score'] ]


total_reviews = len(games_df)
for i in xrange(total_reviews):
    game = games_df.loc[i, 'game_name']
    game = game.replace('-', ' ').strip()
    games_df.loc[i, 'excerpt'] = game
