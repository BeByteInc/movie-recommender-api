from multiprocessing import cpu_count



ROOT_PATH="/Users/bytewaiser/Dev/BeByte/MovieRecommender/movie-recommender-api"

# Socket Path

bind = f'unix:/{ROOT_PATH}/gunicorn.sock'

# Worker Options

workers = cpu_count() + 1

worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options

loglevel = 'debug'

accesslog = f'{ROOT_PATH}/access_log'

errorlog = f'{ROOT_PATH}/error_log'
