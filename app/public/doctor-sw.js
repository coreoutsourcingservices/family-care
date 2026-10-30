/* No clinical responses are cached. This worker only handles opt-in Web Push. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('push', event => {
  let notice;
  try { notice = event.data?.json(); } catch { notice = null; }
  if (!notice || typeof notice.id !== 'string') return;
  const url = new URL(typeof notice.path === 'string' ? notice.path : '/doctor/dashboard', self.location.origin);
  const path = url.origin === self.location.origin && url.pathname.startsWith('/doctor/') ? url.pathname + url.search : '/doctor/dashboard';
  event.waitUntil(Promise.all([
    self.registration.showNotification(notice.title || 'FamilyCare+', {
      body: notice.body || 'You have a new doctor account update.', icon: '/doctor-icon-192.png',
      badge: '/doctor-icon.svg', tag: `familycare-doctor-${notice.id}`, data: { path },
    }),
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
      for (const client of clients) client.postMessage({ type: 'doctor-push', id: notice.id });
    }),
  ]));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const candidate = new URL(event.notification.data?.path || '/doctor/dashboard', self.location.origin);
  const target = candidate.origin === self.location.origin && candidate.pathname.startsWith('/doctor/') ? candidate.href : self.location.origin + '/doctor/dashboard';
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async clients => {
    const existing = clients.find(client => new URL(client.url).pathname.startsWith('/doctor/'));
    if (existing) { await existing.navigate(target); return existing.focus(); }
    return self.clients.openWindow(target);
  }));
});
