import path # type: ignore
import pandas as pd

class MovieService:
    def __init__(self) -> None:
        self.df: pd.DataFrame
        self.df = pd.read_parquet(path.movie_data_path)

    def get_movie(self):
        temp = self.df.sample(1).drop("genre_ids", axis=1).to_dict(orient="records")[0]
        return temp

