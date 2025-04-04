import '../css/settings.css'
import {websocketRequest} from "./websocket";
import Variable from "./variable";


function drawSettingsWindow(settings) {
    return `
        <form id="settings-form">
          <div class="form-group" style="display: none">
            <label>
              <input type="checkbox" name="display_active" ${(settings.display_active) ? 'checked' : ''}>
              Не гасить экран
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" name="notifications" ${(settings.notifications) ? 'checked' : ''}>
              Уведомления в игре
            </label>
          </div>
          <div class="buttons">
            <button type="submit" id="save-settings-btn">Сохранить</button>
          </div>
        </form>
    `;
}

function events() {
    document.querySelector('#settings-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        let object = {
            display_active: document.querySelector('input[name="display_active"]').checked ? 1 : 0,
            notifications: document.querySelector('input[name="notifications"]').checked ? 1 : 0
        };
        await websocketRequest('/settings', {
            'action': 'save',
            'settings': JSON.stringify(object)
        }).then(async response => {
            if (response && response.saved === true) {
                Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
                await applySettings(Variable.getSelfInfo().settings);
                const registration = await navigator.serviceWorker.ready;
                if (object.notifications) {
                    // Подписываемся на push-уведомления
                    const subscription = await registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: urlBase64ToUint8Array(Variable.publicVapidKey)
                    });
                    await websocketRequest('/webpush', {
                        'action': 'subscribe',
                        'subscription': JSON.stringify(subscription)
                    }).then(() => {
                        console.log('Подписка отправлена на сервер.');
                    });
                } else {
                    if ('serviceWorker' in navigator) {
                        const subscription = await registration.pushManager.getSubscription();
                        console.log(subscription);
                        if (subscription) {
                            await subscription.unsubscribe();
                            await websocketRequest('/webpush', {
                                'action': 'unsubscribe',
                                'subscription_endpoint': subscription.endpoint
                            }).then(async () => {
                                console.log('Подписка на уведомления удалена.');
                            });
                        }
                    }
                }
            }
        });
        return false;
    });
    return true;
}

let wakeLock = null;

async function applySettings(settings) {
    if (settings && settings.display_active && settings.display_active === 1) {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('Wake Lock активирован');
            wakeLock.addEventListener('release', () => {
                console.log('Wake Lock деактивирован');
            });
        } catch (err) {
            console.error('Ошибка активации Wake Lock:', err);
        }
    }
}

// Функция преобразования ключа
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

const Settings = {
    drawSettingsWindow,
    events,
    applySettings
}

export default Settings;