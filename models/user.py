from pydantic import BaseModel

class AuthDetails(BaseModel):
    email: str
    username: str
    password: str
    verification_code: int
