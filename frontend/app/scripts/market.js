import '../css/market.css'
import {websocketRequest} from "./websocket";
import Modal from "./modal";
import Utils from "./utils";
import showCreateLotModal from './market_create_lot';
import Variable from "./variable";

/**
 * Форматирует оставшееся время до окончания лота.
 * @param {string} expiresAt - Дата окончания лота в формате ISO.
 * @returns {string} - Строка с оставшимся временем (например, "2 дн. 5 ч. 30 мин.").
 */
function formatRemainingTime(expiresAt) {
    const now = new Date();
    const expiration = new Date(expiresAt);
    const diffMs = expiration - now;
    if (diffMs <= 0) {
        return 'Истёк';
    }
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    let result = '';
    if (diffDays > 0) result += `${diffDays} дн. `;
    if (diffHours > 0) result += `${diffHours} ч. `;
    if (diffMinutes > 0) result += `${diffMinutes} мин.`;
    return result.trim();
}

async function get_lots() {
    return await websocketRequest('/market', {action: 'get_lots'})
        .then(lots => lots)
        .catch(error => {
            console.log(error);
            return null;
        });
}

async function draw() {
    let strLots = '';
    const lots = await get_lots();
    if (lots && lots.length > 0) {
        lots.forEach(lot => {
            // Рассчитываем оставшееся время до окончания лота
            const remaining = formatRemainingTime(lot.expires_at);
            strLots += `
                <div class="item-row" data-name="${lot.item_data.name}" data-level="${lot.item_data.tier}" data-type="${lot.item_data.type}">
                    ${Utils.drawItem(lot.item_data)}
                    <div class="item-details">
                      <span><strong>${lot.item_data.name}</strong></span>
                      <span>Ур.: ${lot.item_data.tier} | Тип: ${lot.item_data.item_type}</span>
                      <div class="silver" title="Серебро">${lot.price}</div>
                    </div>
                    <div class="item-details">
                      <span class="expires" data-expires-at="${lot.expires_at}" title="Время до окончания лота">${remaining}</span>
                    </div>
                    <div class="item-actions">
                      <button class="buy-btn" data-lot-id="${lot.id}">Купить</button>
                    </div>
                </div>
            `;
        });
    }

    Modal.showModal('Рынок', `
        <div class="container-market">
            <!-- Компактная панель фильтра -->
            <div class="filter-panel">
              <div class="filter-header" id="filterToggle">
                <h2>Фильтр товаров</h2>
                <span id="toggleIcon">&#9660;</span> <!-- Стрелка вниз -->
              </div>
              <div class="filter-content" id="filterContent">
                <input type="text" id="filterName" placeholder="Название предмета">
                <input type="number" id="filterLevel" placeholder="Уровень">
                <select id="filterType">
                  <option value="">Все типы</option>
                  <option value="weapon">Оружие</option>
                  <option value="armor">Броня</option>
                  <option value="tool">Инструменты</option>
                  <option value="resource">Ресурсы</option>
                </select>
                <button id="filterBtn">Применить фильтр</button>
              </div>
            </div>
            <div class="item-actions">
                <button id="createLotButton">Создать лот</button>
                <button id="myLotButton">Мои лоты</button>
            </div>
            <div class="item-list" id="itemList">${(strLots) ? strLots : 'Рынок пуст. Приходите позже.'}</div>
          </div>
    `, loadEvents);
    // Запускаем обновление обратного отсчёта
    startCountdownUpdater();
}

const loadEvents = () => {
// Обработчик для сворачивания/разворачивания панели фильтра
    document.getElementById('filterToggle').addEventListener('click', function () {
        const filterContent = document.getElementById('filterContent');
        const toggleIcon = document.getElementById('toggleIcon');
        if (filterContent.classList.contains('active')) {
            filterContent.classList.remove('active');
            toggleIcon.innerHTML = "&#9660;"; // Стрелка вниз
        } else {
            filterContent.classList.add('active');
            toggleIcon.innerHTML = "&#9650;"; // Стрелка вверх
        }
    });

    // Функция фильтрации товаров по введённым параметрам
    document.getElementById('filterBtn').addEventListener('click', function () {
        const filterName = document.getElementById('filterName').value.toLowerCase();
        const filterLevel = document.getElementById('filterLevel').value;
        const filterType = document.getElementById('filterType').value.toLowerCase();

        const items = document.querySelectorAll('.item-row');
        items.forEach(item => {
            const name = item.getAttribute('data-name').toLowerCase();
            const level = item.getAttribute('data-level');
            const type = item.getAttribute('data-type').toLowerCase();

            let visible = true;
            if (filterName && !name.includes(filterName)) {
                visible = false;
            }
            if (filterLevel && level !== filterLevel) {
                visible = false;
            }
            if (filterType && type !== filterType) {
                visible = false;
            }
            item.style.display = visible ? 'flex' : 'none';
        });
    });

    // Пример обработчиков нажатия для кнопок "Купить" и "Лот"
    document.querySelectorAll('.buy-btn').forEach(button => {
        button.addEventListener('click', function () {
            const lot_id = button.getAttribute('data-lot-id');
            Modal.openConfirmModal(async () => {
                await websocketRequest(`/market`, {'action': 'buy', lot_id}).then(response => {
                    console.log(response);
                }).catch(error => {
                    console.log(error);
                });
            });
        });
    });

    // При нажатии на кнопку "Создать лот"
    document.getElementById('createLotButton').addEventListener('click', function () {
        showCreateLotModal(Variable.getSelfInfo().items);
    });
}

/**
 * Функция, которая обновляет содержимое всех элементов с обратным отсчётом.
 */
function updateCountdowns() {
    const countdownElements = document.querySelectorAll('.expires[data-expires-at]');
    countdownElements.forEach(el => {
        const expiresAt = el.getAttribute('data-expires-at');
        if (expiresAt) {
            el.innerText = formatRemainingTime(expiresAt);
        }
    });
}

/**
 * Запускает периодическое обновление обратного отсчёта (каждую секунду).
 */
function startCountdownUpdater() {
    // Сразу обновляем, затем каждые 1000 мс
    updateCountdowns();
    setInterval(updateCountdowns, 1000);
}

const Market = {
    draw,
    get_lots
}

export default Market;
