"""Raw WebSocket gateway. Tickets are sent in the first frame, never in a URL."""
import asyncio
import json
import os
from http import HTTPStatus
from sqlalchemy import select, func
from websockets.asyncio.server import serve
from app import create_app
from core.database import db
from core.models import AppNotification
from services.notifications import socket_user, serialize, count, scan_due

app=create_app({'DB_POOL_SIZE':1,'DB_MAX_OVERFLOW':0})

def snapshot(token=None,claims=None,after=None):
    with app.app_context():
        user,claims=socket_user(token,claims)
        if after is None:return user.id,claims,db().scalar(select(func.max(AppNotification.id))) or 0,[],count(user.id)
        rows=db().scalars(select(AppNotification).where(AppNotification.user_id==user.id,AppNotification.id>after).order_by(AppNotification.id).limit(100)).all()
        return user.id,claims,rows[-1].id if rows else after,[serialize(row) for row in rows],count(user.id)

async def connection(ws):
    if ws.request.path!='/ws/notifications':await ws.close(1008,'Invalid path');return
    try:
        first=json.loads(await asyncio.wait_for(ws.recv(),5))
        if first.get('type')!='auth' or not isinstance(first.get('ticket'),str):raise ValueError()
        user,claims,last,_,unread=await asyncio.to_thread(snapshot,first['ticket'])
        await ws.send(json.dumps({'type':'ready','user_id':user,'resync':True}))
        for _ in range(450):
            await asyncio.sleep(2)
            _,_,last,rows,current=await asyncio.to_thread(snapshot,None,claims,last)
            for row in rows:await ws.send(json.dumps({'type':'notification','notification':row}))
            if current!=unread:
                unread=current;await ws.send(json.dumps({'type':'unread_count','unread_count':current}))
        await ws.close(4000,'Reconnect to continue')
    except Exception:
        await ws.close(4401,'Sign in or reconnect')

async def handshake(connection,request):
    origin=request.headers.get('Origin')
    if origin and origin not in app.config['CORS_ORIGINS']:
        return connection.respond(HTTPStatus.FORBIDDEN,'Origin not allowed')

def scan():
    with app.app_context():scan_due()

async def reminders():
    while True:
        try:await asyncio.to_thread(scan)
        except Exception:pass  # API diagnostics expose readiness; never log medical payloads.
        await asyncio.sleep(60)

async def main():
    async with serve(connection,'127.0.0.1',int(os.getenv('NOTIFICATION_PORT','5002')),process_request=handshake,max_size=4096,ping_interval=20,ping_timeout=20):
        await reminders()

if __name__=='__main__':asyncio.run(main())
