import path
import pandas as pd
from models.movie import Movie, SimpleMovie, SimpleMovieList

class MovieService:
    def __init__(self) -> None:
        self.df = pd.read_parquet(path.movie_data_path)
        self.df.genres = self.df.genres.apply(lambda arr: arr.tolist())
        self.simple_movie_model_attributes = ["id", "title", "genre_names", "poster_path", "vote_average"]
        self.movie_model_attributes = [
                "id", "title", "original_title", "overview", "genre_names", "release_date",
                "original_language", "poster_path", "backdrop_path", "vote_average", "vote_count"
        ]
        self.data_amount_per_page = 10

    def get_movie_by_id(self, id: int) -> Movie:
        data = self.df.loc[self.df.id == id, self.movie_model_attributes]
        data = data.to_dict(orient="records")[0]
        movie = Movie(
            id=data.get("id"),
            original_title=data.get("original_title"),
            title=data.get("title"),
            overview=data.get("overview"),
            genre_names=data.get("genre_names"),
            release_date=data.get("release_date"),
            original_language=data.get("original_language"),
            poster_path=data.get("poster_path"),
            backdrop_path=data.get("backdrop_path"),
            vote_average=data.get("vote_average"),
            vote_count=data.get("vote_count")
        )
        return movie

    def get_data_by_genre_name(self, genre_name: str):
        return self.df.loc[self.df.genre_names.str.lower().str.contains(genre_name.lower())]

    def get_top_rated(self, df: pd.DataFrame, page: int):
        # Page starts from 1
        amount = self.data_amount_per_page
        data = df[self.simple_movie_model_attributes].iloc[(page-1)*amount:page*amount]
        data = data.to_dict(orient="records")
        movie_list = [
                SimpleMovie(
                    id=entry.get("id"),
                    title=entry.get("title"),
                    genre_names=entry.get("genre_names"),
                    poster_path=entry.get("poster_path"),
                    vote_average=entry.get("vote_average")
                ) for entry in data
        ]
        return SimpleMovieList(movie_list=movie_list)

    def get_top_rated_movies(self, page: int):
        return self.get_top_rated(self.df, page)

    def get_top_rated_movies_by_genre_name(self, page: int, genre_name: str):
        df = self.get_data_by_genre_name(genre_name)
        return self.get_top_rated(df, page)
    
    def search_by_title(self, df: pd.DataFrame, search_key: str):
        data = df.loc[df.title.str.lower().str.contains(search_key.lower()) | df.original_title.str.lower().str.contains(search_key.lower()), self.simple_movie_model_attributes]
        data = data.to_dict(orient="records")
        movie_list = [
                SimpleMovie(
                    id=entry.get("id"),
                    title=entry.get("title"),
                    genre_names=entry.get("genre_names"),
                    poster_path=entry.get("poster_path"),
                    vote_average=entry.get("vote_average")
                ) for entry in data
        ]
        return SimpleMovieList(movie_list=movie_list)

    def search_by_title_all_data(self, search_key: str):
        return self.search_by_title(self.df, search_key)

    def search_by_title_with_genre_name(self, search_key: str, genre_name: str):
        df = self.get_data_by_genre_name(genre_name)
        return self.search_by_title(df, search_key)
