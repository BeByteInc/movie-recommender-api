from typing import List
from pydantic import BaseModel
from datetime import datetime

class Movie(BaseModel):
    id: int
    original_title: str
    title: str
    overview: str
    genre_names: str
    release_date: datetime
    original_language: str
    poster_path: str
    backdrop_path: str
    vote_average: float
    vote_count: int

class SimpleMovie(BaseModel):
    id: int
    title: str
    genre_names: str
    poster_path: str

class SimpleMovieList(BaseModel):
    movie_list: List[SimpleMovie] 
