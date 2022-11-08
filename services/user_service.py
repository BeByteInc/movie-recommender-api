import path # type: ignore
import pandas as pd
import numpy as np
from models.movie import Movie, SimpleMovie, SimpleMovieList
from scipy import sparse
from implicit.als import AlternatingLeastSquares
from typing import Dict, Tuple, List

def create_map(arr: np.ndarray) -> Tuple[Dict[int, int], Dict[int, int]]:
    item_to_id = dict(zip(arr, range(len(arr))))
    id_to_item = dict(zip(item_to_id.values(), item_to_id.keys()))
    return item_to_id, id_to_item

class RecommendationService:
    def __init__(self):
        self.ratings = pd.read_parquet(path.recommendation_data_path)
        self.user_to_id, self.id_to_user = create_map(self.ratings.user_id.unique())
        self.movie_to_id, self.id_to_movie = create_map(self.ratings.movie_id.unique())
        self.data = self.get_sparse_data()

    def get_sparse_data(self) -> sparse.csr_matrix:
        ratings_mapped = self.ratings.assign(
            user_id = self.ratings.user_id.map(self.user_to_id),
            post_id = self.ratings.movie_id.map(self.movie_to_id),
        )
        ratings_pivot = sparse.csr_matrix(ratings_mapped.pivot_table(values="liked", index="user_id", columns="movie_id", fill_value=0))
        return ratings_pivot

    def create_model(self):
        self.model = AlternatingLeastSquares(factors=64, regularization=0.05, alpha=2)
        self.model.fit(self.data)

    def recommend(self, n: int) -> SimpleMovieList:
        user_ids = list(self.id_to_user.keys())
        ids, _ = self.model.recommend(user_ids, self.data[user_ids], N=n)

