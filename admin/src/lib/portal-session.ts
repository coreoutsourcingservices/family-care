export type Portal = 'admin' | 'superadmin';
export function portalCookies(portal:Portal){
 return {access:`fc_${portal}_access`,refresh:`fc_${portal}_refresh`,csrf:`fc_${portal}_csrf`};
}
export function currentPortal():Portal{
 return typeof window!=='undefined'&&/^\/superadmin(?:\/|$)/.test(window.location.pathname)?'superadmin':'admin';
}
export function portalLogin(portal:Portal,reason:'expired'|'changed'){
 return `${portal==='superadmin'?'/superadmin':'/'}?session=${reason}`;
}
