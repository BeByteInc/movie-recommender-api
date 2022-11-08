import path # type: ignore
import pandas as pd
import numpy as np
from models.movie import SimpleMovie, SimpleMovieList
from models.recommendation import RecommendationResult
from models.user import UserDetails
from scipy import sparse
from implicit.als import AlternatingLeastSquares
from typing import Dict, Tuple, List

def create_map(arr: np.ndarray) -> Tuple[Dict[int, int], Dict[int, int]]:
    item_to_id = dict(zip(arr, range(len(arr))))
    id_to_item = dict(zip(item_to_id.values(), item_to_id.keys()))
    return item_to_id, id_to_item

class RecommendationService:
    def __init__(self):
        self.userdata = pd.read_csv(path.user_database_path).iloc[1:] # First data is admin
        self.moviedata = pd.read_parquet(path.movie_data_path)

        likedata = pd.read_parquet(path.recommendation_data_path)
        self.base_like_count = likedata.movie_id.apply(len).sum()

    def set_user_likes(self, user: UserDetails) -> RecommendationResult:
        user_id = self.userdata[self.userdata.username == user.username].id.item()
        data = pd.DataFrame([{"user_id": user_id, "movie_id": user.movie_list}])
        
        likedata = pd.read_parquet(path.recommendation_data_path)
        likedata = pd.concat([likedata, data], axis=0, ignore_index=True)
        likedata.to_parquet(path.recommendation_data_path)
        self.recommend_dict = self.recommend_all()
        return self.recommend(user.username)

    def create_recommendation_data(self):
        likedata = pd.read_parquet(path.recommendation_data_path)
        like_sum = likedata.movie_id.apply(len).sum()

        self.recdata = pd.merge(likedata.user_id, likedata.movie_id.explode(), left_index=True, right_index=True)
        self.recdata["liked"] = 1
        self.user_to_id, self.id_to_user = create_map(self.recdata.user_id.unique())
        self.movie_to_id, self.id_to_movie = create_map(self.recdata.movie_id.unique())

        self.first_run = False
        self.base_like_count = like_sum

    def get_sparse_data(self) -> sparse.csr_matrix:
        self.create_recommendation_data()
        ratings_mapped = self.recdata.assign(
            user_id = self.recdata.user_id.map(self.user_to_id),
            post_id = self.recdata.movie_id.map(self.movie_to_id),
        )
        ratings_pivot = sparse.csr_matrix(ratings_mapped.pivot_table(values="liked", index="user_id", columns="movie_id", fill_value=0))
        return ratings_pivot

    def create_model(self, data):
        model = AlternatingLeastSquares(factors=64, regularization=0.05, alpha=2)
        model.fit(data)
        return model

    def recommend_all(self, n: int=100) -> Dict[str, List[int]]:
        data = self.get_sparse_data()
        model = self.create_model(data)
        user_ids = np.array([self.user_to_id.get(i) for i in self.userdata.id.tolist()])
        ids, _ = model.recommend(user_ids, data[user_ids], N=n)
        result = dict(zip(self.userdata.username.tolist(), ids.tolist()))
        return result

    def recommend(self, username: str) -> RecommendationResult:
        res = self.recommend_dict.get(username)
        movie_data = self.moviedata[self.moviedata.id.isin(np.array(res))]
        movie_data["vote_average"] = movie_data["vote_average"].round(2)
        movie_data = movie_data.to_dict(orient="records")
        movie_list = [
            SimpleMovie(
                id=entry.get("id"),
                title=entry.get("title"),
                genre_names=entry.get("genre_names"),
                poster_path=entry.get("poster_path"),
                vote_average=entry.get("vote_average")
            ) for entry in movie_data
        ] 
        recommends = SimpleMovieList(movie_list=movie_list)
        return RecommendationResult(username=username, recommendation=recommends)
