from app import create_app
from app.utils.file_processing import celery

app = create_app()

if __name__ == '__main__':
    celery.start()