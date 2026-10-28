"""Run with Flask's Python; heavy OCR executes in the isolated OCR Python."""
import argparse,time
from app import create_app
from core.database import db
from services.report_text import process_one

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    app=create_app()
    while True:
        with app.app_context():
            try:worked=process_one()
            except Exception as error:
                db().rollback();app.logger.warning('Report worker unavailable: %s',type(error).__name__);worked=False
        if args.once:return
        if not worked:time.sleep(2)

if __name__=='__main__':main()
