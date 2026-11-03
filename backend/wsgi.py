from app import create_app

app = create_app()
from scripts.recycle_worker import start_background
start_background(app)

# Start per serving process on its first request, including preloaded Gunicorn workers.
@app.before_request
def start_recycle_worker():
    start_background(app)
