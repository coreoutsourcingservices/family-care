import asyncio
import json
import pytest
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed,InvalidStatus
from test_care import patient

def test_real_websocket_delivery_origin_and_session_revocation(app,client,monkeypatch):
    import scripts.notification_socket as gateway
    monkeypatch.setattr(gateway,'app',app)
    headers=patient(app,client)
    ticket=client.post('/api/v1/notifications/socket-ticket',headers=headers,json={}).json['ticket']
    async def scenario():
        async with serve(gateway.connection,'127.0.0.1',0,process_request=gateway.handshake) as server:
            port=server.sockets[0].getsockname()[1]
            url=f'ws://127.0.0.1:{port}/ws/notifications'
            with pytest.raises(InvalidStatus):
                async with connect(url,origin='https://untrusted.example',proxy=None):pass
            async with connect(url,origin='http://localhost:3000',proxy=None) as ws:
                await ws.send(json.dumps({'type':'auth','ticket':ticket}))
                ready=json.loads(await asyncio.wait_for(ws.recv(),5))
                assert ready['type']=='ready' and ready['resync'] is True
                result=await asyncio.to_thread(client.post,'/api/v1/notifications/test',headers=headers,json={})
                assert result.status_code==201
                event=json.loads(await asyncio.wait_for(ws.recv(),6))
                assert event['type']=='notification'
                assert event['notification']['id']==result.json['notification']['id']
                assert json.loads(await asyncio.wait_for(ws.recv(),3))['type']=='unread_count'
                await asyncio.to_thread(client.post,'/api/v1/auth/logout',headers=headers)
                with pytest.raises(ConnectionClosed) as closed:
                    await asyncio.wait_for(ws.recv(),6)
                assert closed.value.rcvd.code==4401
    asyncio.run(scenario())
