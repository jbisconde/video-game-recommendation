from get_data import get_data_from_mongodb
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import NMF
from SVD import MatrixFactorizationRecommender

def get_ratings_contents():
    games_df = get_data_from_mongodb()
    game_names = pd.factorize(games_df.game_name)
    critics = pd.factorize(games_df.critic)

    ratings_contents = games_df[ ['score'] ].astype(int)
    ratings_contents.loc[:, 'game'] = pd.Series(game_names[0])
    ratings_contents.loc[:, 'user'] = pd.Series(critics[0])

    return ratings_contents

def get_ratings_data(ratings_contents):
    total_users = len(ratings_contents.user.unique())
    total_games = len(ratings_contents.game.unique())
    ratings_mat = sparse.lil_matrix((total_users, total_games))

    for _, row in ratings_contents.iterrows():
        ratings_mat[row.user, row.game] = row.score

    return ratings_mat

def validation(recommender, ratings_mat, pct_users_to_val=0.82, pct_items_to_val=0.82):
    n_users = ratings_mat.shape[0]
    n_items = ratings_mat.shape[1]
    n_users_in_val = int(n_users * pct_users_to_val)
    n_items_in_val = int(n_items * pct_items_to_val)
    val_data = ratings_mat[:n_users_in_val, :n_items_in_val].copy()
    train_data = ratings_mat.copy()
    train_data[:n_users_in_val, :n_items_in_val] = 0
    recommender.fit(train_data)

    # Printing MSE (With Avg)
    preds = recommender.pred_all_users()
    val_preds = preds[:n_users_in_val, :n_items_in_val]
    print (mse_sparse_with_dense(val_data, val_preds))

def mse_sparse_with_dense(sparse_mat, dense_mat):
    """
    Computes mean-squared-error between a sparse and a dense matrix.  Does not include the 0's from
    the sparse matrix in computation (treats them as missing)
    """
    # get mask of non-zero, mean-square of those, divide by count of those
    nonzero_idx = sparse_mat.nonzero()
    mse = (np.array(sparse_mat[nonzero_idx] - dense_mat[nonzero_idx]) ** 2).mean()
    return mse

def validate_recommendation_model():
    ratings_contents = get_ratings_contents()

    ratings_mat = get_ratings_data(ratings_contents)

    my_mf_rec_engine = MatrixFactorizationRecommender()
    validation(my_mf_rec_engine, ratings_mat)
