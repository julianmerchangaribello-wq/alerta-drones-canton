/* ============================================================
   Service Worker - SARM Militar (Despierta con pantalla bloqueada)
   ============================================================ */

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// EVENTO PUSH DEL SERVIDOR EN LA NUBE (DESPIERTA EL CELULAR/TABLET EN REPOSO)
self.addEventListener('push', (event) => {
  let data = {
    title: '🚨 ¡ATAQUE DE DRON DETECTADO!',
    body: 'TOMAR CUBIERTA INMEDIATA. SIRENA MILITAR ACTIVA.',
    url: '/sismo_drones.html'
  };

  try {
    if (event.data) {
      data = Object.assign(data, event.data.json());
    }
  } catch (e) {}

  const options = {
    body: data.body,
    icon: '/icon-drone-512.png',
    badge: '/icon-drone-192.png',
    tag: 'alerta-militar-dron',
    renotify: true,
    requireInteraction: true, // Se queda fija hasta que se atienda
    silent: false,
    vibrate: [800, 200, 800, 200, 1000, 300, 1500],
    data: { url: data.url }
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// CLIC EN LA NOTIFICACIÓN: ENCIENDE Y ABRE LA APP DIRECTAMENTE
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const urlToOpen = event.notification.data ? event.notification.data.url : '/sismo_drones.html';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});
