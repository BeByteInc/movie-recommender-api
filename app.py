from models.result import Result
from models.user import AuthDetails
from services.movie_service import MovieService
from services.auth_service import AuthHandler
from fastapi import FastAPI, Depends, HTTPException
import pandas as pd
import uvicorn

app = FastAPI()
auth_handler = AuthHandler()

user_database_path = "resources/datasets/logindata.parquet"

@app.post("/register", status_code=201)
def register(auth_details: AuthDetails):
    user_database = pd.read_parquet(user_database_path)
    if (user_database.username == auth_details.username).sum() > 0:
        raise HTTPException(status_code=400, detail='Username is taken')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    user_database.append({
        "id": user_database.id.max() + 1,
        "username": auth_details.username,
        "password": hashed_password,
        "verification_code": auth_details.verification_code
    }, ignore_index=True).to_parquet(user_database_path, index=False)
    token = auth_handler.encode_token(auth_details.username)
    return {"token": token}

@app.post("/login")
def login(auth_details: AuthDetails):
    user_database = pd.read_parquet(user_database_path)
    data = user_database[user_database.username == auth_details.username].to_dict(orient="records")
    print(data)
    user = None if len(data) == 0 else data[0]
    if (user is None) or (not auth_handler.verify_password(auth_details.password, user["password"])):
        raise HTTPException(status_code=401, detail="Invalid username and/or password")
    token = auth_handler.encode_token(user["username"])
    return { "token": token }

movie_service = MovieService()
@app.get("/get_movie_by_id", response_model=Result)
async def get_movie_by_id(id: int, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="Movie", function=movie_service.get_movie_by_id, id=id)

@app.get("/get_top_rated_movies", response_model=Result)
async def get_top_rated_movies(page:int, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=movie_service.get_top_rated_movies, page=page)

@app.get("/get_top_rated_movies_by_genre_name", response_model=Result)
async def get_top_rated_movies_by_genre_name(page: int, genre_name: str, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=movie_service.get_top_rated_movies_by_genre_name, page=page, genre_name=genre_name)

@app.get("/search_by_title_all_data", response_model=Result)
async def search_by_title_all_data(search_key: str, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=movie_service.search_by_title_all_data, search_key=search_key)

@app.get("/search_by_title_with_genre_name", response_model=Result)
async def search_by_title_with_genre(search_key: str, genre_name: str, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=movie_service.search_by_title_with_genre_name, search_key=search_key, genre_name=genre_name)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, host="0.0.0.0")
