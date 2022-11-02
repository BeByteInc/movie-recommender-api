from models.result import Result
from services.movie_service import MovieService
from fastapi import FastAPI
import uvicorn

app = FastAPI()


movie_service = MovieService()

@app.get("/get_movie_by_id", response_model=Result)
def get_movie_by_id(id: int):
    return Result.build(type="Movie", function=movie_service.get_movie_by_id, id=id)

@app.get("/get_top_rated_movies", response_model=Result)
def get_top_rated_movies(page: int):
    return Result.build(type="SimpleMovieList", function=movie_service.get_top_rated_movies, page=page)

@app.get("/get_top_rated_movies_by_genre_name", response_model=Result)
def get_top_rated_movies_by_genre_name(page: int, genre_name: str):
    return Result.build(type="SimpleMovieList", function=movie_service.get_top_rated_movies_by_genre_name, page=page, genre_name=genre_name)

@app.get("/search_by_title_all_data", response_model=Result)
def search_by_title_all_data(search_key: str):
    return Result.build(type="SimpleMovieList", function=movie_service.search_by_title_all_data, search_key=search_key)

@app.get("/search_by_title_with_genre_name", response_model=Result)
def search_by_title_with_genre(search_key: str, genre_name: str):
    return Result.build(type="SimpleMovieList", function=movie_service.search_by_title_with_genre_name, search_key=search_key, genre_name=genre_name)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
