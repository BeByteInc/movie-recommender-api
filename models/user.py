from typing import Optional, List
from pydantic import BaseModel

class AuthDetails(BaseModel):
    email: Optional[str]
    username: str
    password: str

class UserFavorite(BaseModel):
    user_id: int
    movie_id: int

class UserFavorites(BaseModel):
    user_id: int
    movie_ids: List[int]

class RecommendByGenreModel(BaseModel):
    user_id: int
    genre_names: List[str]
