from models.movie import Movie, SimpleMovieList
from services.movie_service import MovieService
from fastapi import FastAPI

app = FastAPI()


movie_service = MovieService()

@app.get("/get_movie_by_id", response_model=Movie)
def get_movie_by_id(id: int):
    return movie_service.get_movie_by_id(id)

@app.get("/get_top_rated_movies", response_model=SimpleMovieList)
def get_top_rated_movies(page: int):
    return movie_service.get_top_rated_movies(page)

@app.get("/get_top_rated_movies_by_genre_name", response_model=SimpleMovieList)
def get_top_rated_movies_by_genre_name(page: int, genre_name: str):
    return movie_service.get_top_rated_movies_by_genre_name(page, genre_name)

@app.get("/search_by_title_all_data", response_model=SimpleMovieList)
def search_by_title_all_data(key: str):
    return movie_service.search_by_title_all_data(key)

@app.get("/search_by_title_with_genre", response_model=SimpleMovieList)
def search_by_title_with_genre(key: str, genre: str):
    return movie_service.search_by_title_with_genre(key, genre)
