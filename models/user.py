from typing import Optional
from pydantic import BaseModel

class AuthDetails(BaseModel):
    email: Optional[str]
    username: str
    password: str
