import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    from doctor.push_worker import start
    start(app)
    from waitress import serve
    serve(app, host='127.0.0.1', port=int(os.getenv('PORT', '5001')), threads=8)
