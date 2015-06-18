import numpy as np
import pandas as pd
from scipy import sparse
from time import time
from numpy import matrix
from numpy.random import RandomState, rand


class MatrixFactorizationRec(object):

    def __init__(self, n_features=12, learn_rate=0.05,
                 regularization_param=0.02, optimizer_pct_improvement_criterion=5):
        self.n_features = n_features
        self.learn_rate = learn_rate
        self.regularization_param = regularization_param
        self.optimizer_pct_improvement_criterion = optimizer_pct_improvement_criterion

    def fit(self, ratings_mat):
        self.ratings_mat = ratings_mat
        n_movies = self.ratings_mat.shape[1]

        self.movies_rated = (ratings_mat > 0).sum(axis=1)
        self.avg_ratings = np.zeros( (1, n_movies) )
        total_movies_rated = (ratings_mat > 0).sum(axis=0).astype(float)

        for movie_index in xrange(n_movies):
            if total_movies_rated[:, movie_index] < 4:
                self.ratings_mat[:, movie_index] = 0

        # Calculate the avg ratings
        self.avg_ratings = ratings_mat.sum(axis=0) / total_movies_rated
        self.avg_ratings = np.nan_to_num(self.avg_ratings)
        
        # # Calculate the 90th percentile for rated movies
        # ratings_90_percentile = np.zeros( (1, n_movies) )
        # for movie in xrange(n_movies):
        #     movie_ratings = self.ratings_mat[:, movie].toarray()
        #     movie_ratings = movie_ratings[movie_ratings.nonzero()[0]]
        #     if len(movie_ratings):
        #         ratings_90_percentile[0, movie] = np.percentile(movie_ratings, 90)

        # Subtract the avg ratings to the rating matrix
        #self.ratings_mat = self.ratings_mat - self.avg_ratings
        self.n_users = ratings_mat.shape[0]
        self.n_items = ratings_mat.shape[1]
        self.n_rated = ratings_mat.nonzero()[0].size
        # self.user_mat = matrix(
        #     rand(self.n_users*self.n_features).reshape([self.n_users, self.n_features]))
        # self.movie_mat = matrix(
        #     rand(self.n_items*self.n_features).reshape([self.n_features, self.n_items]))
        rs = RandomState(42)
        self.user_mat = matrix(
            rs.rand(self.n_users*self.n_features).reshape([self.n_users, self.n_features]))
        self.movie_mat = matrix(
            rs.rand(self.n_items*self.n_features).reshape([self.n_features, self.n_items]))
        optimizer_iteration_count = 0
        sse_accum = 0
        print("Optimizaiton Statistics")
        print("Iterations | Mean Squared Error  |  Percent Improvement")
        while ((optimizer_iteration_count < 2) or (pct_improvement > self.optimizer_pct_improvement_criterion)):
            old_sse = sse_accum
            sse_accum = 0
            for i in range(self.n_users):
                for j in range(self.n_items):
                    if self.ratings_mat[i, j] > 0:
                        error = self.ratings_mat[i, j] - np.dot(self.user_mat[i, :], self.movie_mat[:, j])
                        sse_accum += error ** 2
                        for k in range(self.n_features):
                            self.user_mat[i, k] = self.user_mat[i, k] + self.learn_rate * \
                                (2 * error * self.movie_mat[k, j] - self.regularization_param * self.user_mat[i, k])
                            self.movie_mat[k, j] = self.movie_mat[k, j] + self.learn_rate * \
                                (2 * error * self.user_mat[i, k] - self.regularization_param * self.movie_mat[k, j])
            pct_improvement = 100 * (old_sse - sse_accum) / (old_sse)
            print("%d \t\t %f \t\t %f" % (
                optimizer_iteration_count, sse_accum / self.n_rated, pct_improvement))
            old_sse = sse_accum
            optimizer_iteration_count += 1
        print("Fitting of latent feature matrices completed")

    def pred_all_users(self, report_run_time=False):
        start_time = time()
        if report_run_time:
            print("Execution time: %f seconds" % (time()-start_time))

        out = np.zeros( (self.n_users, self.n_items) )
        thresholds = [5, 24, 102]
        pop_weightings = [1, .67, .33, 0]

        # If they haven't seen about 5 movies, give them the average prediction (ratings)
        for user_id in xrange(self.n_users):
            user_out = self.user_mat[user_id] * self.movie_mat + self.avg_ratings
            if self.movies_rated[user_id] < thresholds[0]: 
                out[user_id] = self.avg_ratings

            elif self.movies_rated[user_id] < thresholds[1]: 
                out[user_id] = self.avg_ratings * pop_weightings[1] + \
                    user_out * (1 - pop_weightings[1])

            elif self.movies_rated[user_id] < thresholds[2]: 
                out[user_id] = self.avg_ratings * pop_weightings[2] + \
                    user_out * (1 - pop_weightings[2])

            else:
                out[user_id] = user_out

        return out

    def pred_all_users_wo_avg(self, report_run_time=False):
        start_time = time()
        out = self.user_mat * self.movie_mat

        if report_run_time:
            print("Execution time: %f seconds" % (time()-start_time))
        return out

    def top_n_popularity(self, n):
        item_index_sorted_by_avg_rating = list(np.argsort(self.avg_ratings))
        return item_index_sorted_by_avg_rating[-n:]

    def top_n_recs(self, user_id, n):
        pred_ratings = self.pred_one_user(user_id)
        item_index_sorted_by_pred_rating = list(np.argsort(pred_ratings))
        items_rated_by_this_user = self.ratings_mat[user_id].nonzero()[1]
        unrated_items_by_pred_rating = [item for item in item_index_sorted_by_pred_rating
                                        if item not in items_rated_by_this_user]
        return unrated_items_by_pred_rating[-n:]
