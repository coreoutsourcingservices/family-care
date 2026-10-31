"""Synthetic admin recovery browser fixture; never sends SMTP or reads real accounts."""
from frontend_fixture import app
from flask import jsonify
from sqlalchemy import select
from core.database import db
from core.models import OTPChallenge,User
from services.otp import otp_code

app.config['CORS_ORIGINS']+=['http://localhost:3005','http://127.0.0.1:3005']

@app.get('/__test/reset-code')
def reset_code():
    user=db().scalar(select(User).where(User.email=='admin@example.com'))
    row=db().scalar(select(OTPChallenge).where(OTPChallenge.user_id==user.id,OTPChallenge.purpose=='reset_password').order_by(OTPChallenge.created_at.desc()).limit(1))
    return jsonify(otp=otp_code(row.id))

if __name__=='__main__':
    from waitress import serve
    serve(app,host='127.0.0.1',port=5510,threads=1)
