/*
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service_worker.js')
        .then(async (registration) => {
            console.log('Service Worker зарегистрирован.');
            await navigator.serviceWorker.ready;
            console.log('Service Worker активирован.');
            // Запрос разрешения на уведомления
            Notification.requestPermission().then((permission) => {
                if (permission === 'granted') {
                    console.log('Разрешение на уведомления получено');
                }
            });

            if (!('PeriodicSyncManager' in window)) {
                console.warn('Periodic Sync API не поддерживается в вашем браузере.');
            }

            // Регистрация периодической синхронизации
            registration.update().then(() => {
                if ('periodicSync' in registration) {
                    registration.sync.register('send-coordinates', {
                        minInterval: 15 * 60 * 1000 // Интервал: 15 минут
                    }).then(() => {
                        console.log('Периодическая синхронизация зарегистрирована');
                    }).catch((err) => {
                        console.error('Ошибка регистрации периодической синхронизации:', err);
                    });
                }
            });
        })
        .catch(error => console.error('Ошибка регистрации Service Worker:', error));
}
*/
