from models.movie import Movie
from services.movie_service import MovieService
from typing import Union
from fastapi import FastAPI

app = FastAPI()


movie_service = MovieService()

@app.get("/get_movie", response_model=Movie)
def get_movie():
    return movie_service.get_movie()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
