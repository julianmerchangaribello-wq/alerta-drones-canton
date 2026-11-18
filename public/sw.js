/* ============================================================
   Service Worker - SARM (Sistema Táctico de Alerta Temprana)
   Comandancia: MY. JULIAN CAMILO MERCHAN GARIBELLO
   Operación 24/7 en Segundo Plano y Notificaciones de Emergencia
   ============================================================ */

const CACHE_NAME = 'sarm-militar-v3';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Escucha mensajes de la aplicación para disparar notificaciones de emergencia persistentes
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'TRIGGER_EMERGENCY') {
    self.registration.showNotification('🚨 ¡ALERTA ROJA DE DRON EN EL CANTÓN!', {
      body: 'AMENAZA AÉREA INMINENTE. TOMAR CUBIERTA INMEDIATA.\nAutorizado: MY. JULIAN CAMILO MERCHAN GARIBELLO',
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      tag: 'drone-emergency',
      renotify: true,
      requireInteraction: true, // Se queda fija hasta que el oficial la atienda
      silent: false,
      vibrate: [800, 200, 800, 200, 800, 200, 1200],
      data: { url: '/sismo_drones.html' }
    });
  } else if (event.data && event.data.type === 'CLEAR_EMERGENCY') {
    self.registration.getNotifications({ tag: 'drone-emergency' }).then((notifications) => {
      notifications.forEach((n) => n.close());
    });
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow('/sismo_drones.html');
    })
  );
});
