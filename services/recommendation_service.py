import path # type: ignore
import pandas as pd
import numpy as np
from models.movie import SimpleMovie, SimpleMovieList
from scipy import sparse
from implicit.als import AlternatingLeastSquares
from typing import Dict, Tuple, List
import sqlite3

def create_map(arr: np.ndarray) -> Tuple[Dict[int, int], Dict[int, int]]:
    item_to_id = dict(zip(arr, range(len(arr))))
    id_to_item = dict(zip(item_to_id.values(), item_to_id.keys()))
    return item_to_id, id_to_item

class RecommendationService:
    def __init__(self):
        pass

    def get_user(self, username):
        conn = sqlite3.connect(path.database)
        user = conn.execute("SELECT id, password FROM users WHERE username is ?", (username,)).fetchone()
        conn.close()
        return user

    def register_user(self, email: str, username: str, password: str):
        conn = sqlite3.connect(path.database) # Tables => (users, movies)
        conn.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)", (email, username, password))
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE username is ?", (username,)).fetchone()
        conn.close()
        return user_id

    def set_user_favorites(self, user_id: int, movie_ids: List[int]):# -> SimpleMovieList:
        movie_ids_string = "|".join([str(i) for i in movie_ids])
        conn = sqlite3.connect(path.database) # Tables => (users, movies)
        conn.execute("UPDATE users SET movie_id=(?) WHERE id=(?)", (movie_ids_string, user_id))
        conn.commit()
        conn.close()
        
        # self.recommend_dict = self.recommend_all()
        # return self.recommend(user_id)

    def get_user_favorites(self, user_id: int) -> SimpleMovieList:
        conn = sqlite3.connect(path.database) # Tables => (users, movies)
        movie_ids_string = conn.execute("SELECT movie_id FROM users WHERE id is ?", (user_id,)).fetchone()[0]

        if movie_ids_string is None:
            return SimpleMovieList(movie_list=[])

        movie_data = []
        for movie_id in movie_ids_string.split("|"):
            movie_data.append(conn.execute("SELECT id, title, genre_names, poster_path, vote_average FROM movies WHERE id is (?)", (int(movie_id),)).fetchone())

        conn.close()
        movie_list = [
            SimpleMovie(
                id=entry[0],
                title=entry[1],
                genre_names=entry[2],
                poster_path=entry[3],
                vote_average=entry[4]
            ) for entry in movie_data
        ] 
        return SimpleMovieList(movie_list=movie_list)

    def add_user_favorites(self, user_id: int, movie_id: int):
        conn = sqlite3.connect(path.database) # Tables => (users, movies)
        movie_ids_string = conn.execute("SELECT movie_id FROM users WHERE id is ?", (user_id,)).fetchone()[0]
        movie_ids_string += f"|{movie_id}"
        conn.execute("UPDATE users SET movie_id=(?) WHERE id=(?)", (movie_ids_string, user_id))
        conn.commit()
        conn.close()
    
    def remove_user_favorites(self, user_id: int, movie_id: int):
        conn = sqlite3.connect(path.database) # Tables => (users, movies)
        movie_ids_string = conn.execute("SELECT movie_id FROM users WHERE id is ?", (user_id,)).fetchone()[0]
        movie_ids = [i for i in movie_ids_string.split("|") if i != str(movie_id)]
        movie_ids_string = "|".join(movie_ids)
        conn.execute("UPDATE users SET movie_id=(?) WHERE id=(?)", (movie_ids_string, user_id))
        conn.commit()
        conn.close()

    def get_sparse_data(self) -> sparse.csr_matrix:
        conn = sqlite3.connect(path.database) # Tables => (users, movies)
        self.user_data = conn.execute("SELECT id, movie_id FROM USERS").fetchall()
        conn.close()
        recdata = pd.DataFrame(data = self.user_data, columns=["user_id", "movie_ids"])
        recdata = recdata.assign(
                favorite = 1,
                movie_ids = lambda df: df.movie_ids.apply(lambda x: [int(i) for i in x.split("|")])
        ).pipe(lambda df: df.explode("movie_ids"))

        self.user_to_id, self.id_to_user = create_map(recdata.user_id.unique())
        self.movie_to_id, self.id_to_movie = create_map(recdata.movie_ids.unique())

        ratings_mapped = recdata.assign(
            user_id = recdata.user_id.map(self.user_to_id),
            movie_ids = recdata.movie_ids.map(self.movie_to_id),
        )
        ratings_pivot = sparse.csr_matrix(ratings_mapped.pivot_table(values="favorite", index="user_id", columns="movie_ids", fill_value=0))
        return ratings_pivot

    def recommend_all(self, n: int=100) -> Dict[int, List[int]]:
        data = self.get_sparse_data()
        model = AlternatingLeastSquares(factors=64, regularization=0.05, alpha=2)
        model.fit(data)
        if (self.userdata.favorites_set == True).sum() == 0:
            return {}
        users = self.userdata[self.userdata.favorites_set == True]
        user_ids = np.array([self.user_to_id.get(i) for i in users.id.tolist()])
        ids, _ = model.recommend(user_ids, data[user_ids], N=n, filter_already_liked_items=True)
        result = dict(zip(users.id.tolist(), ids.tolist()))
        return result

    def recommend(self, user_id: int) -> SimpleMovieList:
        res = self.recommend_dict.get(user_id)
        if res is None:
            return SimpleMovieList(movie_list=[])
        
        user_favorites = self.favdata.loc[self.favdata.user_id == user_id].movie_id.iloc[0]
        res = [i for i in res if not i in user_favorites]

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
            return SimpleMovieList(movie_list=[])
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
