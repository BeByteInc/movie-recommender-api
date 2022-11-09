from typing import Optional, List
from pydantic import BaseModel

class AuthDetails(BaseModel):
    email: Optional[str]
    username: str
    password: str
    favorites_set: Optional[bool]

class UserDetails(BaseModel):
    username: str
    movie_list: List[int]
