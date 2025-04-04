import '../css/market_create_lot.css'
import {websocketRequest} from "./websocket";
import Modal from "./modal";
import Utils from "./utils";

/**
 * Показывает модальное окно для создания лота.
 * @param {Array} inventoryItems - Массив объектов предметов из инвентаря игрока.
 */
function showCreateLotModal(inventoryItems) {
    // Разметка модального окна:
    const modalContent = `
    <div id="createLotModal" class="create-lot-modal">
      <!-- Верхняя часть: компактная форма создания лота -->
      <div class="lot-creation-section">
        <div id="selectedItemContainer" class="selected-item">
          <!-- Изначально показывается сообщение с просьбой выбрать предмет -->
          <p class="placeholder">Выберите предмет из инвентаря</p>
        </div>
        <div class="lot-form-inline">
          <input type="number" id="lotPrice" name="lotPrice" placeholder="Цена" required min="1" />
          <input type="number" id="lotQuantity" name="lotQuantity" placeholder="Кол-во" required min="1" value="1" />
          <button id="createLotBtn" class="modal-confirm">Выставить</button>
        </div>
      </div>
      <!-- Нижняя часть: сетка предметов инвентаря -->
      <div class="inventory-grid">
          ${inventoryItems.filter(item => !item.is_equipped).map(item => Utils.drawItem(item)).join('')}
      </div>
    </div>
    `;

    Modal.showModal('Создание лота', modalContent, () => {
        // При клике по предмету из инвентаря запоминаем его и отображаем в верхней части
        document.querySelectorAll('[data-item-id]').forEach(itemEl => {
            itemEl.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation(); // предотвращаем всплытие события
                const itemId = parseInt(this.getAttribute('data-item-id'));
                const selectedItem = inventoryItems.find(item => item.item_id === itemId);
                if (selectedItem) {
                    // Отобразить выбранный предмет в верхней части компактно
                    const container = document.getElementById('selectedItemContainer');
                    container.innerHTML = Utils.drawItem(selectedItem);
                    // Сохраняем id выбранного предмета для последующей отправки
                    container.setAttribute('data-selected-item-id', selectedItem.user_item_id);
                }
                return false;
            });
        });

        // Обработчик нажатия кнопки "Выставить"
        document.getElementById('createLotBtn').addEventListener('click', async function () {
            const selectedContainer = document.getElementById('selectedItemContainer');
            const selectedItemId = selectedContainer.getAttribute('data-selected-item-id');
            if (!selectedItemId) {
                Utils.createToast('Пожалуйста, выберите предмет из инвентаря для продажи.');
                return;
            }
            const price = parseInt(document.getElementById('lotPrice').value);
            const quantity = parseInt(document.getElementById('lotQuantity').value, 10);
            if (!price || price <= 0 || !quantity || quantity <= 0) {
                Utils.createToast('Пожалуйста, введите корректные данные для цены и количества.');
                return;
            }
            await websocketRequest('/market', {'action': 'create_lot', item_id: selectedItemId, price, quantity})
                .then(response => {
                    console.log(response);
                    if (response?.created && response?.created === true) {
                        Modal.closeModalHandler();
                    }
                }
            ).catch(error => {
                console.log(error);
            });
        });
    });
}

export default showCreateLotModal;
