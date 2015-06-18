import math
import numpy as np
import pandas as pd
from scipy import sparse

def get_ratings_data():
    ratings_contents = pd.read_table("../data/u.data",
                                     names=["user", "movie", "rating", "timestamp"])
    highest_user_id = ratings_contents.user.max()
    highest_movie_id = ratings_contents.movie.max()
    ratings_as_mat = sparse.lil_matrix((highest_user_id, highest_movie_id))
    for _, row in ratings_contents.iterrows():
        # subtract 1 from id's due to match 0 indexing
        ratings_as_mat[row.user-1, row.movie-1] = row.rating
    return ratings_contents, ratings_as_mat


class MatrixFactorizationRecommender(object):
    """Basic framework for a matrix factorization class.

    You may find it useful to write some additional internal  methods for purposes
    of code cleanliness etc.
    """
    
    def __init__(self, 
                n_features=12, 
                learn_rate=0.05,
                regularization_param=0.02,
                optimizer_pct_improvement_criterion=5):
        """Init should set all of the parameters of the model
        so that they can be used in other methods.
        """
        self.n_features = n_features
        self.learn_rate = learn_rate
        self.regularization_param = regularization_param
        self.optimizer_pct_improvement_criterion = optimizer_pct_improvement_criterion
        self.user_mat = None
        self.movie_mat = None

    def fit(self, ratings_mat):
        """Like the scikit learn fit methods, this method 
        should take the ratings data as an input and should
        compute and store the matrix factorization. It should assign
        some class variables like n_users, which depend on the
        ratings_mat data.

        It can return nothing
        """
        self.user_mat, self.movie_mat = self.matrix_factorization(ratings_mat)

    def matrix_factorization(self, sparse_matrix):
        ratings_mat = sparse_matrix.toarray()
        n_users, n_movies = ratings_mat.shape
        n_already_rated = ratings_mat.nonzero()[0].size

        user_mat = np.random.random( (n_users, self.n_features) )
        movie_mat = np.random.random( (self.n_features, n_movies) )

        optimizer_iteration_count = 0
        sse_accum = 0

        print("Optimizaiton Statistics")
        print("Iterations | Mean Squared Error  |  Percent Improvement")

        while (optimizer_iteration_count < 2 or (pct_improvement > self.optimizer_pct_improvement_criterion)):
            old_sse = sse_accum
            sse_accum = 0
            for i in range(n_users):

                for j in range(n_movies):
                    if ratings_mat[i, j] > 0:
                        error = ratings_mat[i, j] - np.dot(user_mat[i, :], movie_mat[:, j])
                        sse_accum += error ** 2

                        user_mat[i, :], movie_mat[:, j] = self.update_user_movie_matrix(user_mat[i, :], 
                                                                        movie_mat[:, j], error)
                        # for k in range(self.n_features):
                        #     user_mat[i, k] = user_mat[i, k] + 
                        #                         self.learn_rate * 
                        #                             (2 * error * movie_mat[k, j] - 
                        #                             self.regularization_param * user_mat[i, k])
                        #     movie_mat[k, j] = movie_mat[k, j] + 
                        #                         self.learn_rate * 
                        #                             (2 * error * user_mat[i, k] - 
                        #                             self.regularization_param * movie_mat[k, j])

            pct_improvement = 100 * (old_sse - sse_accum) / old_sse
            print("%d \t\t %f \t\t %f" % (
                optimizer_iteration_count, sse_accum / n_already_rated, pct_improvement))
            old_sse = sse_accum
            optimizer_iteration_count += 1
        # ensure these are matrices so multiplication works as intended
        return np.matrix(user_mat), np.matrix(movie_mat)

    def update_user_movie_matrix(self, user_mat, movie_mat, error):
        for k in range(self.n_features):
            user_mat[k] = user_mat[k] + \
                                self.learn_rate * \
                                    (2 * error * movie_mat[k] - \
                                    self.regularization_param * user_mat[k])
            movie_mat[k] = movie_mat[k] + \
                                self.learn_rate * \
                                    (2 * error * user_mat[k] - \
                                    self.regularization_param * movie_mat[k])

        return user_mat, movie_mat

    def pred_one_user(self, user_id):
        """Returns the predicted rating for a single
        user.
        """
        return self.user_mat[user_id] * self.movie_mat
    
    def pred_all_users(self):
        """Returns the predicted rating for all users/items.
        """
        return self.user_mat*self.movie_mat

    def top_n_recs(self, ratings_mat, user_id, num):
        """Returns the top n recs for a given user.
        """
        n_already_rated = ratings_mat[user_id,:].nonzero()[0]
        predictions = self.pred_one_user(user_id).argsort()[:,::-1]
        already_rated_predictions = np.in1d(predictions, n_already_rated)
        predictions_not_rated = predictions[:, ~already_rated_predictions]
        return predictions_not_rated[:, :num]

def main():
    print 'Creating Recommender Model'
    rec = MatrixFactorizationRecommender()
    print '...'
    print 'Importing Data'
    ratings_data_contents, ratings_mat = get_ratings_data()
    print '...'
    print 'Running Fit'
    rec.fit(ratings_mat)
    print '...'
    print 'Predict One User'
    user_1_preds = rec.pred_one_user(user_id =1)
    # Show predicted ratings for user #1
    print user_1_preds
    print '...'
    print 'Top Recommendations'
    top_recs = rec.top_n_recs(ratings_mat, user_id = 1, num = 10)
    print top_recs
    print '...'
    print 'Predict All User'
    all_user_preds = rec.pred_all_users()
    print all_user_preds


if __name__ == '__main__':
    main()