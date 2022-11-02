from pydantic.generics import GenericModel
from typing import Optional, Union
from .movie import Movie, SimpleMovie, SimpleMovieList

class Result(GenericModel):
    status: Optional[str]
    error_message: Optional[str]
    item_list: Optional[Union[Movie, SimpleMovie, SimpleMovieList]]
    type: str

    def clean(self):
        return self.dict(exclude_none=True)

    @staticmethod
    def build(type, function, **kwargs):
        try:
            result = Result(type=type, item_list=function(**kwargs),
                            status='Success').clean()
        except Exception as ex:
            print(str(ex))
            result = Result(type=type, status='Fail',
                            error_message=str(ex))
        return result
