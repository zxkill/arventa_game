import Toastify from "toastify-js"
import "toastify-js/src/toastify.css";
import {Circle, Fill, Icon, Stroke, Style, Text} from 'ol/style';
import Polygon from 'ol/geom/Polygon';
import Feature from 'ol/Feature';
import {fromLonLat} from 'ol/proj';
import {Point} from 'ol/geom';
import {Vector as VectorSource} from 'ol/source';
import {Vector as VectorLayer} from 'ol/layer';
import Variable from "./variable";

function createTextStyle(item) {
    return new Text({
        font: '10px Arial',
        text: item.name,
        fill: new Fill({color: '#ffffff'}),
        stroke: new Stroke({color: '#000000', width: 3}),
        offsetY: -17,
    });
}

function createIconStyle(src, width = 32, height = 32) {
    return new Icon({
        src: src,
        width: width,
        height: height,
    });
}

function createCircleStyle(color, radius = 10) {
    return new Circle({
        radius: radius,
        fill: new Fill({color: color}),
    });
}

function redirectToAuth() {
    if (window.location.href !== 'https://' + window.location.host + '/') {
        window.location.href = "/";
    }
}

function loadGamePage() {
    if (window.location.href !== 'https://' + window.location.host + '/game.html') {
        window.location.href = "/game.html";
    }
}

function logout() {
    localStorage.clear();
    redirectToAuth();
}

function transformCoordinates(coords) {
    let [lat, lon] = coords.split(',');
    lat = lat.slice(0, -1);
    lon = lon.slice(0, -1);
    return `${lat},${lon}`;
}

function createToast(text = '', duration = 3000) {
    Toastify({
        text: text,
        escapeMarkup: false,
        duration: duration,
        gravity: "bottom",
        position: "right",
        stopOnFocus: true,
        style: {
            background: "linear-gradient(to right, #333, #1e1e1e)",
            border: '2px solid #333'
        },
    }).showToast();
}

function isMobile() {
    if ('maxTouchPoints' in navigator) return navigator.maxTouchPoints > 0
    else if ('msMaxTouchPoints' in navigator) return navigator.msMaxTouchPoints > 0
    else if ('orientation' in window) return true
    else return /\b(BlackBerry|webOS|iPhone|IEMobile|Android|Windows Phone|iPad|iPod)\b/i.test(navigator.userAgent)
}

let healthTimer = null;

function updateStatusBar(selfInfo) {
    if (healthTimer) {
        clearInterval(healthTimer);
        healthTimer = null;
    }

    document.querySelector('#avatar').setAttribute('src', selfInfo.profile.avatar);
    document.querySelector('#nickname').innerHTML = `${selfInfo.name}`;

    let health = (selfInfo.attributes.cur_health * 100) / selfInfo.attributes.max_health;
    let energy = (selfInfo.attributes.cur_energy * 100) / selfInfo.attributes.max_energy;

    document.querySelector('#user_health').style.width = health + '%';
    document.querySelector('#user_energy').style.width = energy + '%';

    document.querySelector('#user_health_digital').innerHTML = selfInfo.attributes.cur_health + '/' + selfInfo.attributes.max_health;
    document.querySelector('#user_energy_digital').innerHTML = selfInfo.attributes.cur_energy + '/' + selfInfo.attributes.max_energy;

    const healthRecoveryPerSecond = selfInfo.attributes.recovery_health / 60;
    const energyRecoveryPerSecond = selfInfo.attributes.recovery_energy / 60;

    const lastUpdated = parseInt(selfInfo.attributes.last_updated);

    healthTimer = setInterval(() => {
        const currentTime = Math.floor(Date.now() / 1000);
        const elapsedSeconds = currentTime - lastUpdated;

        if (selfInfo.attributes.cur_health < selfInfo.attributes.max_health) {
            const newHealth = Math.min(
                selfInfo.attributes.cur_health + healthRecoveryPerSecond * elapsedSeconds,
                selfInfo.attributes.max_health
            );
            let percent_health = (newHealth * 100) / selfInfo.attributes.max_health;
            document.querySelector('#user_health').style.width = percent_health + '%';
            document.querySelector('#user_health_digital').innerHTML = (percent_health * selfInfo.attributes.max_health) / 100 + '/' + selfInfo.attributes.max_health;
        }

        if (selfInfo.attributes.cur_energy < selfInfo.attributes.max_energy) {
            const newEnergy = Math.min(
                selfInfo.attributes.cur_energy + energyRecoveryPerSecond * elapsedSeconds,
                selfInfo.attributes.max_energy
            );
            let percent_energy = (newEnergy * 100) / selfInfo.attributes.max_energy;
            document.querySelector('#user_energy').style.width = percent_energy + '%';
            document.querySelector('#user_energy_digital').innerHTML = (percent_energy * selfInfo.attributes.max_energy) / 100 + '/' + selfInfo.attributes.max_health;
        }
    }, 1000);
}

function splitItemsIntoStacks(items) {
    const processedItems = [];
    const equippedItems = []; // Для надетых предметов

    items.forEach(item => {
        // Если предмет не стакается
        if (item.is_equipped) {
            // Надетый предмет добавляем в список экипировки
            equippedItems.push(item);
        } else {
            // Остальные — в инвентарь
            processedItems.push(item);
        }
    });

    return {inventory: processedItems, equipped: equippedItems};
}

function drawItem(item) {
    let quantity = '';
    let item_not_allowed = false;
    if (item.quantity && item.quantity > 0) {
        quantity = `<span class="reward-quantity">x${item.quantity}</span>`;
    }
    if (item.type === 'tool' || item.type === 'armor' || item.type === 'weapon' || item.type === 'resource') {
        Variable.getSelfInfo()?.skill_progress.forEach(progress => {
            if ((item.type === progress.type_item) && (item.resource_type === progress.type_resource) && (item.tier > progress.current_level)) {
                item_not_allowed = true;
            } else if ((item.type === 'resource') && (progress.type_item === 'craft') && (item.resource_type === progress.type_resource) && (item.tier > progress.current_level)) {
                item_not_allowed = true;
            }
        })
    }
    return `
        <div class="reward-item" data-item-id="${item.item_id}">
          <div class="reward-icon-container"${(item_not_allowed) ? ' style="background-color:#ff000066"' : ''}>
            <img data-src="img/icons/items/${item.item_id}.png?${new Date().getDate()}" src="" alt="${item.name}" class="reward-icon lazy" data-item='${JSON.stringify(item)}'>
          </div>
          ${quantity}
        </div>
    `
}

function drawItemInfo(item, display_button = 'flex') {
    let effects = '';
    if (item.effect && Object.keys(item.effect).length > 0) {
        effects = `
            <p>Дополнительные эффекты:<br>
                ${(item.effect) ? Object.entries(item.effect).map(([name, value]) => `${name}: +${value}`).join('<br>') : 'Нет'}</p>
        `;
    }
    return `
        <div class="modal-header">
            <span class="modal-title">${item.name}</span>
            <span class="modal-close">&times;</span>
        </div>
        <div class="modal-content-item">
            <p>${item.description}</p>
            <p>Уровень предмета: ${item.tier}</p>
            <p>${(item.damage) ? 'Урон: ' + item.damage : (item.armor) ? 'Защита: ' + item.armor : ''}</p>
            ${(item.durability) ? '<p>Прочность: ' + item.durability + '/1000</p>' : ''}
            <p>Вес: ${item.weight}</p>
            ${effects}
            <div class="inventory-item-button" style="display: ${display_button}">
                ${(item.is_equippetable && !item.is_equipped) ? '<button data-item-action-equip>Надеть</button>' : ''}
                ${(item.is_equippetable && item.is_equipped) ? '<button data-item-action-equip>Снять</button>' : ''}
                <button data-item-action-destroy>Уничтожить</button>
            </div>
        </div>
    `;
}

function drawEquipment(items) {
    const slots = {
        neck: 'Амулет',
        helmet: 'Шлем',
        cloak: 'Плащ',
        right_hand: 'Правая рука',
        body: 'Броня',
        left_hand: 'Левая рука',
        gloves: 'Перчатки',
        boots: 'Ботинки',
        bag: 'Сумка'
    };
    // Создаем объект, где ключ — часть тела, значение — предмет или null
    const equipment = {};
    Object.keys(slots).forEach(slot => equipment[slot] = null);
    // Заполняем объект экипировки
    items.forEach(item => {
        if (item.is_equipped && item.body_part in equipment) {
            equipment[item.body_part] = item;
        }
    });
    // Генерируем разметку для всех слотов
    return Object.keys(slots).map(bodyPart => {
        const item = equipment[bodyPart];
        if (item) {
            // Если слот заполнен, отображаем предмет
            return `<div data-item-body-part="${bodyPart}">${drawItem(item)}</div>`;
        } else {
            // Если слот пустой, отображаем название слота
            return `<div data-item-body-part="${bodyPart}">${slots[bodyPart]}</div>`;
        }
    }).join('');
}

function drawCharacterWindows(character) {
    let divItem = '';
    let equipment = '';
    let items;
    if (character.items) {
        items = character.items;
    }
    // Разбиваем предметы на стеки и разделяем их на экипированные и в инвентаре
    const {inventory, equipped} = splitItemsIntoStacks(items);
    equipment = drawEquipment(equipped);
    // Рисуем инвентарь
    for (let i = 0; i < 100; i++) {
        if (inventory[i]) {
            divItem += drawItem(inventory[i]);
        } else {
            divItem += '<div class="reward-item"></div>';
        }
    }
    let weight = (character.attributes.cur_weight * 100) / character.attributes.max_weight;
    return `
        <div class="player-window">
            <!-- Экипировка -->
            <div class="equipment">
                ${equipment}
            </div>
            <!-- Атрибуты -->
            <div class="attributes">
                <div class="attribute">Здоровье: <span>${character.attributes.max_health}</span></div>
                <div class="attribute">Восст. здоровья: <span>${character.attributes.recovery_health}/м</span></div>
                <div class="attribute">Энерегия: <span>${character.attributes.max_energy}</span></div>
                <div class="attribute">Восст. энергии: <span>${character.attributes.recovery_energy}/м</span></div>
                <div class="attribute">Макс. вес: <span>${character.attributes.max_weight}</span></div>
                <div class="attribute">Урон: <span>${character.attributes.attack}</span></div>
                <div class="attribute">Защита: <span>${character.attributes.defense}</span></div>
                <div class="attribute">Шанс крита: <span>${character.attributes.crit_chance}</span></div>
                <div class="attribute">Шанс уклонения: <span>${character.attributes.evasion_chance}</span></div>
                <div class="attribute">Сила: <span>${character.attributes.strength}</span></div>
                <div class="attribute">Ловкость: <span>${character.attributes.dexterity}</span></div>
                <div class="attribute">Интеллект: <span>${character.attributes.intelligence}</span></div>
                <div class="attribute">Выносливость: <span>${character.attributes.endurance}</span></div>
                <div class="attribute">Удача: <span>${character.attributes.luck}</span></div>
                <div class="attribute">
                    <div class="silver" title="Серебро">${character.silver}</div>
                </div>
            </div>
            <div class="progress-weight">
                <div class="weight" id="user_weight" style="width: ${weight}%;"></div>
                <div class="progress-weight-text">${character.attributes.cur_weight}/${character.attributes.max_weight}</div>
            </div>
            <!-- Инвентарь -->
            <div class="inventory">
                <div class="inventory-grid">
                    ${divItem}
                </div>
            </div>
        </div>
    `;
}

function addRegionsToMap(map, regions) {
    const features = [];

    regions.forEach(region => {
        const topLeft = JSON.parse(region.top_left).coordinates;
        const bottomRight = JSON.parse(region.bottom_right).coordinates;

        // Вычисляем центр квадрата
        const centerLat = (topLeft[1] + bottomRight[1]) / 2;
        const centerLon = (topLeft[0] + bottomRight[0]) / 2;

        // Преобразуем координаты в формат OpenLayers
        const topLeftLonLat = fromLonLat(topLeft);
        const bottomRightLonLat = fromLonLat(bottomRight);
        const centerLonLat = fromLonLat([centerLon, centerLat]);

        // Создаем углы квадрата
        const topRight = [bottomRightLonLat[0], topLeftLonLat[1]];
        const bottomLeft = [topLeftLonLat[0], bottomRightLonLat[1]];

        // Создаем Polygon
        const polygon = new Polygon([[topLeftLonLat, topRight, bottomRightLonLat, bottomLeft, topLeftLonLat]]);
        const polygonFeature = new Feature({geometry: polygon});

        polygonFeature.setStyle(
            new Style({
                stroke: new Stroke({color: 'rgba(73,253,2,0.85)', width: 1}),
            }),
        );

        // Создаем текстовую метку
        const textFeature = new Feature({
            geometry: new Point(centerLonLat)
        });

        textFeature.setStyle(
            new Style({
                text: new Text({
                    text: region.name || 'Unnamed',
                    font: '18px sans-serif',
                    fill: new Fill({color: '#000'}),
                    stroke: new Stroke({color: '#fff', width: 2}),
                    scale: 1 // По умолчанию
                })
            })
        );

        features.push(polygonFeature);
        features.push(textFeature);
    });

    // Создаем источник и слой
    const vectorSource = new VectorSource({
        features: features
    });

    const vectorLayer = new VectorLayer({
        source: vectorSource
    });

    // Добавляем слой на карту
    map.addLayer(vectorLayer);

    // Обновляем размер текста при изменении масштаба карты
    map.getView().on('change:resolution', function () {
        const zoom = map.getView().getZoom();
        const scale = Math.max(0.6, zoom / 7); // Подбираем пропорциональную зависимость
        vectorSource.getFeatures().forEach(feature => {
            const style = feature.getStyle();
            if (style && style.getText()) {
                style.getText().setScale(scale);
            }
        });
    });
}

function preventSleep() {
    const audio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=');
    audio.loop = true;
    audio.play().catch(console.error);
}

// Настройки для Observer (можно кастомизировать)
const observerOptions = {
    root: null, // Наблюдаем относительно viewport
    rootMargin: '100px', // Загрузка начнется за 200px до появления в зоне видимости
    threshold: 0.1 // Минимальная часть элемента, которая должна быть видна
};

// Создаем Observer
const imgObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) { // Если изображение в зоне видимости
            const img = entry.target;
            // Подменяем атрибуты
            img.src = img.dataset.src;
            img.onload = () => img.classList.add('loaded'); // Добавляем класс после загрузки
            if (img.dataset.srcset) img.srcset = img.dataset.srcset;
            img.classList.remove('lazy'); // Убираем класс, если нужно
            observer.unobserve(img); // Прекращаем наблюдение
        }
    });
}, observerOptions);

function observeNewImages() {
    const newImages = document.querySelectorAll('img.lazy:not(.loaded)');
    newImages.forEach(img => {
        img.classList.add('loaded');
        imgObserver.observe(img);
    });
    return true;
}

// Группировка экспорта
const Utils = {
    redirectToAuth,
    drawItemInfo,
    loadGamePage,
    createTextStyle,
    createIconStyle,
    createCircleStyle,
    createToast,
    updateStatusBar,
    transformCoordinates,
    drawCharacterWindows,
    logout,
    drawItem,
    addRegionsToMap,
    isMobile,
    preventSleep,
    observeNewImages
};

export default Utils;