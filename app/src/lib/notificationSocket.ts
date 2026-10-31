import {ApiError,refreshSession} from './authApi';
import {careApi} from './careApi';

/** Tickets travel in the first frame, never in URLs or browser storage. */
export function connectDoctorNotifications(onUpdate:()=>void,onState:(state:string)=>void){
  let stopped=false,socket:WebSocket|undefined,timer:ReturnType<typeof setTimeout>|undefined,delay=1000;
  const schedule=()=>{if(stopped)return;timer=setTimeout(connect,delay);delay=Math.min(delay*2,30000);};
  async function connect(){
    if(stopped)return;
    onState('Connecting');
    try{
      const {ticket}=await careApi<{ticket:string}>('/notifications/socket-ticket',{});
      if(stopped)return;
      const url=import.meta.env.VITE_NOTIFICATION_WS_URL??`${location.protocol==='https:'?'wss':'ws'}://${location.hostname}${import.meta.env.DEV?':5002':location.port?':'+location.port:''}/ws/notifications`;
      socket=new WebSocket(url);
      socket.onopen=()=>{if(!stopped)socket?.send(JSON.stringify({type:'auth',ticket}));};
      socket.onmessage=event=>{
        if(stopped)return;
        try{
          const message=JSON.parse(event.data);
          if(message.type==='ready'){delay=1000;onState('Live');onUpdate();}
          else if(message.type==='notification'||message.type==='unread_count')onUpdate();
        }catch{/* REST polling resynchronizes the inbox if an event is malformed. */}
      };
      socket.onclose=event=>{
        if(stopped)return;
        onState('Reconnecting');
        if(event.code===4401)void refreshSession('doctor').then(schedule).catch(()=>{if(!stopped)onState('Sign in required');});
        else schedule();
      };
      socket.onerror=()=>socket?.close();
    }catch(error){
      if(stopped)return;
      if(error instanceof ApiError&&[401,403].includes(error.status)){onState('Sign in required');return;}
      onState('Refreshing periodically');schedule();
    }
  }
  void connect();
  return()=>{stopped=true;if(timer)clearTimeout(timer);socket?.close();};
}
