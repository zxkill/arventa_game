const CACHE_NAME = 'game-cache-v3';
const ASSETS = [
    '/'
];

// Установка Service Worker и кэширование
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
    console.log('Service Worker установлен');
});

// Обновление Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    console.log('Service Worker активирован');
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || fetch(event.request);
        })
    );
});

// Обработка пуш-уведомлений
self.addEventListener('push', (event) => {
    console.log(event.data);
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Новое событие!';
    const options = {
        body: data.body || 'Откройте игру, чтобы узнать больше!',
        icon: '/apple-icon-180x180.png',
        badge: '/apple-icon-180x180.png'
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Получение координат и отправка на сервер
async function sendCoordinatesToServer(coords) {
    //await apiRequest('/player/coordinates', 'POST', null, coords);
}

// Периодическая задача
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'send-coordinates') {
        event.waitUntil(
            navigator.geolocation.getCurrentPosition(
                (position) => sendCoordinatesToServer(position.coords),
                (error) => console.error('Ошибка получения координат:', error)
            )
        );
    }
});
