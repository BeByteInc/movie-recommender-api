import path # type: ignore
import pandas as pd
import numpy as np
from models.movie import SimpleMovie, SimpleMovieList
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
        self.userdata = pd.read_csv(path.user_database_path) # [id: int, email: str, username: str, password: str, favorites_set: bool]
        self.moviedata = pd.read_parquet(path.movie_data_path) 
        self.likedata = pd.read_parquet(path.recommendation_data_path) # [user_id: int, movie_id: List[int]]
        self.username_to_user_id = self.userdata.set_index("username")["id"].to_dict()
        self.recommend_dict = self.recommend_all()

    def set_user_likes(self, user: UserDetails) -> SimpleMovieList:
        user_id = self.userdata[self.userdata.username == user.username].id.item()
        data = pd.DataFrame([{"user_id": user_id, "movie_id": user.movie_list}])
        
        self.likedata = pd.concat([self.likedata, data], axis=0, ignore_index=True)
        self.likedata.to_parquet(path.recommendation_data_path)
        self.recommend_dict = self.recommend_all()

        self.userdata.loc[self.userdata.username == user.username, "favorites_set"] = True
        return self.recommend(user.username)

    def get_user_likes(self, username):
        user_id = self.username_to_user_id.get(username)
        movie_list = self.likedata.loc[self.likedata.user_id == user_id].movie_id
        movie_data = self.moviedata[self.moviedata.id.isin(movie_list)].to_dict(orient="records")
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


    def add_user_likes(self, username, movie_id):
        user_id = self.username_to_user_id.get(username)
        user = self.likedata.loc[self.likedata.user_id == user_id]
        movie_list = np.append(user.movie_id, movie_id)
        self.likedata.at[user.name, "movie_id"] = movie_list
    
    def remove_user_likes(self, username, movie_id):
        user_id = self.username_to_user_id.get(username)
        user = self.likedata.loc[self.likedata.user_id == user_id]
        self.likedata.at[user.name, "movie_id"] = user.movie_id[user.movie_id != movie_id]

    def create_recommendation_data(self):
        likedata = pd.read_parquet(path.recommendation_data_path)
        like_sum = likedata.movie_id.apply(len).sum()

        self.recdata = pd.merge(likedata.user_id, likedata.movie_id.explode(), left_index=True, right_index=True)
        self.recdata["liked"] = 1

        self.user_to_id, self.id_to_user = create_map(self.recdata.user_id.unique())
        self.movie_to_id, self.id_to_movie = create_map(self.recdata.movie_id.unique())
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
        users = self.userdata[self.userdata.favorites_set == True]
        user_ids = np.array([self.user_to_id.get(i) for i in users.id.tolist()])
        ids, _ = model.recommend(user_ids, data[user_ids], N=n)
        result = dict(zip(users.username.tolist(), ids.tolist()))
        return result

    def recommend(self, username: str) -> SimpleMovieList:
        res = self.recommend_dict.get(username)
        movie_data = self.moviedata[self.moviedata.id.isin(np.array(res))]
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
        return SimpleMovieList(movie_list=movie_list)
