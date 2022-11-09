import path # type: ignore
import pandas as pd
import numpy as np
from models.movie import SimpleMovie, SimpleMovieList
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
        self.favdata = pd.read_parquet(path.recommendation_data_path) # [user_id: int, movie_id: List[int]]
        self.recommend_dict = self.recommend_all()

    def set_user_favorites(self, user_id: int, movie_ids: List[int]) -> SimpleMovieList:
        if not (self.favdata.user_id == user_id).any():
            data = pd.DataFrame([{"user_id": user_id, "movie_id": movie_ids}])
            self.favdata = pd.concat([self.favdata, data], axis=0, ignore_index=True)
            self.favdata.to_parquet(path.recommendation_data_path)

        self.userdata = pd.read_csv(path.user_database_path) # [id: int, email: str, username: str, password: str, favorites_set: bool]
        self.userdata.loc[self.userdata.id == user_id, "favorites_set"] = True
        self.userdata.to_csv(path.user_database_path, index=False)
        
        self.recommend_dict = self.recommend_all()
        return self.recommend(user_id)

    def get_user_favorites(self, user_id: int) -> SimpleMovieList:
        fav_set = self.userdata.loc[self.userdata.id == user_id, "favorites_set"]
        if fav_set.empty:
            return SimpleMovieList()
        if not fav_set.iloc[0]:
            return SimpleMovieList()
        movie_list = self.favdata.loc[self.favdata.user_id == user_id].movie_id.iloc[0]
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
        return SimpleMovieList(movie_list=movie_list)

    def add_user_favorites(self, user_id: int, movie_id: int):
        user = self.favdata.loc[self.favdata.user_id == user_id].iloc[0]
        movie_list = user.movie_id if movie_id in user.movie_id else np.append(user.movie_id, movie_id)
        self.favdata.at[user.name, "movie_id"] = movie_list
        self.favdata.to_parquet(path.recommendation_data_path)
    
    def remove_user_favorites(self, user_id: int, movie_id: int):
        user = self.favdata.loc[self.favdata.user_id == user_id].iloc[0]
        self.favdata.at[user.name, "movie_id"] = user.movie_id[user.movie_id != movie_id]
        self.favdata.to_parquet(path.recommendation_data_path)

    def create_recommendation_data(self):
        favdata = pd.read_parquet(path.recommendation_data_path)
        fav_sum = favdata.movie_id.apply(len).sum()

        self.recdata = pd.merge(favdata.user_id, favdata.movie_id.explode(), left_index=True, right_index=True)
        self.recdata["favorites"] = 1

        self.user_to_id, self.id_to_user = create_map(self.recdata.user_id.unique())
        self.movie_to_id, self.id_to_movie = create_map(self.recdata.movie_id.unique())
        self.base_favorite_count = fav_sum

    def get_sparse_data(self) -> sparse.csr_matrix:
        self.create_recommendation_data()
        ratings_mapped = self.recdata.assign(
            user_id = self.recdata.user_id.map(self.user_to_id),
            post_id = self.recdata.movie_id.map(self.movie_to_id),
        )
        ratings_pivot = sparse.csr_matrix(ratings_mapped.pivot_table(values="favorites", index="user_id", columns="movie_id", fill_value=0))
        return ratings_pivot

    def create_model(self, data):
        model = AlternatingLeastSquares(factors=64, regularization=0.05, alpha=2)
        model.fit(data)
        return model

    def recommend_all(self, n: int=100) -> Dict[int, List[int]]:
        data = self.get_sparse_data()
        model = self.create_model(data)
        if (self.userdata.favorites_set == True).sum() == 0:
            return {}
        users = self.userdata[self.userdata.favorites_set == True]
        user_ids = np.array([self.user_to_id.get(i) for i in users.id.tolist()])
        ids, _ = model.recommend(user_ids, data[user_ids], N=n)
        result = dict(zip(users.id.tolist(), ids.tolist()))
        return result

    def recommend(self, user_id: int) -> SimpleMovieList:
        res = self.recommend_dict.get(user_id)
        if res is None:
            return SimpleMovieList()
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
    
    def recommend_with_genre(self, user_id: int, genre_names: List[str]) -> SimpleMovieList:
        res = self.recommend_dict.get(user_id)
        if res is None:
            return SimpleMovieList()
        movie_data = self.moviedata[self.moviedata.id.isin(np.array(res))].reset_index(drop=True)
        true_map = pd.Series(data=[True]*len(movie_data))
        for genre in genre_names:
            true_map = (true_map) & (movie_data.genre_names.str.lower().str.contains(genre.lower()))
        movie_data = movie_data[true_map].to_dict(orient="records")
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
