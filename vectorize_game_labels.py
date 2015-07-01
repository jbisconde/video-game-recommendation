import cPickle as pickle
import numpy as np
import pandas as pd
import shlex
from fuzzywuzzy import process as proc
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import defaultdict

with open('data/model.pkl', 'rb') as f_model:
        model = pickle.load(f_model)

with open('data/all_games.pkl', 'rb') as f_all:
        all_games = pickle.load(f_all)

all_games_df = pd.DataFrame(all_games)

game_vocab = all_games_df['game_name'].unique()

search_cond = '"Half-Life" "Portal" -"Resident Evil"'

def find_similar_games(search_cond, game_vocab, model, all_games_df):
    search_dict = defaultdict(list)
    games = []
    all_condition = shlex.split(search_cond)
    for cond in all_condition:

        if cond[0] == '-':
            real_cond = proc.extractOne(cond[1:], game_vocab)
            search_dict['negative'].append(real_cond[0])
        else:
            real_cond = proc.extractOne(cond, game_vocab)
            search_dict['positive'].append(real_cond[0])
            games.append(real_cond[0])

    result = model.most_similar(positive=search_dict['positive'], negative=search_dict['negative'], topn=20)
    games.extend([game[0] for game in result])

    rec_games_data = []
    for game in games:
        # real_games = proc.extractBests(game, game_vocab, score_cutoff=90)
        # for real_game in real_games:
        real_game_data = all_games_df[all_games_df['game_name'] == game].to_dict('record')
        rec_games_data.append(real_game_data[0])

    rec_games_data = check_for_duplicates(rec_games_data)

    return [data['game_name'] for data in rec_games_data]

rec_games = find_similar_games(search_cond, game_vocab, model, all_games_df)

search_array_1 = model['Half-Life'][np.newaxis]
search_array_2 = model['Portal'][np.newaxis]

search_array_3 = model['Resident Evil / biohazard HD REMASTER'][np.newaxis]

search_array_4 = model['SiN Episodes: Emergence'][np.newaxis]

search_array_4 = model['Counter-Strike'][np.newaxis]

search_vectors = np.concatenate((search_array_1, search_array_2, search_array_3, search_array_4), axis=0)

pca = PCA(n_components=2)
search_vectors_pca = pca.fit_transform(search_vectors)

plt.figure()
ax = plt.gca()
ax.quiver((0, 0), (0, 0), search_vectors_pca[0], search_vectors_pca[1], 
    angles='xy', scale_units='xy', scale=1)
ax.axis([-3, 3, -3, 3])

ax2 = plt.gca()
ax2.quiver((0, 0), (0, 0), search_vectors_pca[2], search_vectors_pca[3], 
    angles='xy', scale_units='xy', scale=1)
ax2.axis([-3, 3, -3, 3])
plt.show()

plt.figure()
ax = plt.gca()
ax.quiver((0, 0), (0, 0), search_vectors_pca[3], search_vectors_pca[0] + search_vectors_pca[1] - search_vectors_pca[2], 
    angles='xy', scale_units='xy', scale=1)
ax.axis([-3, 3, -3, 3])
plt.show()
