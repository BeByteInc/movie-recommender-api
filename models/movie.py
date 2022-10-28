from typing import List
from pydantic import BaseModel
from datetime import datetime

class Movie(BaseModel):
    id: int
    original_title: str
    title: str
    overview: str
    release_date: datetime
    original_language: str
    popularity: float
    poster_path: str
    backdrop_path: str
    vote_average: float
    vote_count: int


class MovieList(BaseModel):
    movie_list: List[Movie] 
