from models.result import Result
from models.user import RegisterDetail, LoginDetail, UserFavorite, UserFavorites, RecommendByGenreModel
from services.movie_service import MovieService
from services.auth_service import AuthHandler
from fastapi import FastAPI, Depends, HTTPException
import uvicorn

from services.recommendation_service import RecommendationService

app = FastAPI()
auth_handler = AuthHandler()

movie_service = MovieService()
recommendation_service = RecommendationService()

@app.post("/register", status_code=201)
def register(auth_details: RegisterDetail):
    user = recommendation_service.get_user(auth_details.username)
    if user is not None:
        raise HTTPException(status_code=400, detail='Username is taken')
    
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    token = auth_handler.encode_token(auth_details.username)

    user_id = recommendation_service.register_user(auth_details.email, auth_details.username, hashed_password)[0]

    response = {"username": auth_details.username, "user_id": user_id, "token": token, "item_list": []}
    return response

@app.post("/login")
def login(auth_details: LoginDetail):
    user = recommendation_service.get_user(auth_details.username)

    if (user is None):
        raise HTTPException(status_code=401, detail="Invalid username and/or password")
    if not auth_handler.verify_password(auth_details.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid username and/or password")

    token = auth_handler.encode_token(auth_details.username)

    response = {"username": auth_details.username, "user_id": user[0], "token": token, "item_list": recommendation_service.get_user_favorites(user[0])}
    return response

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

@app.get("/recommend", response_model=Result)
async def recommend(user_id: int, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=recommendation_service.recommend, user_id=user_id)

@app.post("/recommend_by_genre_names", response_model=Result)
async def recommend_by_genre(user: RecommendByGenreModel, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=recommendation_service.recommend_with_genre, user_id=user.user_id, genre_names=user.genre_names)

@app.get("/get_user_favorites", response_model=Result)
async def get_user_favorites(user_id: int, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=recommendation_service.get_user_favorites, user_id=user_id)

@app.post("/set_user_favorites")
async def set_user_favorites(user: UserFavorites, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=recommendation_service.set_user_favorites, user_id=user.user_id, movie_ids=user.movie_ids)

@app.post("/add_to_user_favorites")
async def add_user_favorites(user: UserFavorite,_=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=recommendation_service.add_user_favorites, user_id=user.user_id, movie_id=user.movie_id)

@app.post("/remove_from_user_favorites")
async def remove_user_favorites(user: UserFavorite, _=Depends(auth_handler.auth_wrapper)):
    return Result.build(type="SimpleMovieList", function=recommendation_service.remove_user_favorites, user_id=user.user_id, movie_id=user.movie_id)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, host="0.0.0.0")
