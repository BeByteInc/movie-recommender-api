from typing import List
from pydantic import BaseModel
from models.movie import SimpleMovieList

class RecommendationResult(BaseModel):
    username: str
    recommendation: SimpleMovieList

