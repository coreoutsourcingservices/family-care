"""Run with Flask's Python; heavy OCR executes in the isolated OCR Python."""
import argparse,time
from app import create_app
from core.database import db
from services.report_text import process_one

def start_background(app):
    """Keep local uploads processing when the API is started with server.py."""
    import threading
    if app.extensions.get('report_worker'):return
    def run():
        while True:
            with app.app_context():
                try:worked=process_one()
                except Exception as error:
                    db().rollback();app.logger.warning('Report worker unavailable: %s',type(error).__name__);worked=False
            if not worked:time.sleep(2)
    thread=threading.Thread(target=run,name='report-ocr-worker',daemon=True)
    app.extensions['report_worker']=thread
    thread.start()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    app=create_app({'DB_POOL_SIZE':1,'DB_MAX_OVERFLOW':0})
    while True:
        with app.app_context():
            try:worked=process_one()
            except Exception as error:
                db().rollback();app.logger.warning('Report worker unavailable: %s',type(error).__name__);worked=False
        if args.once:return
        if not worked:time.sleep(2)

if __name__=='__main__':main()
