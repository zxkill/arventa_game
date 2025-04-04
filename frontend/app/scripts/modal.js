import Variable from "./variable";
import Utils from "./utils";
import {websocketRequest} from "./websocket";

const activeModals = new Map(); // Track active modals
const modal = document.querySelector('.info.popup');
const modalContent = document.querySelector('#modal-content');
const modalHeader = document.querySelector('#modal-header');
const modalTitle = document.querySelector('#modal-header .modal-title');
const closeModal = document.querySelector('.close-button');

closeModal.addEventListener('click', closeModalHandler);
closeModal.addEventListener('touchend', closeModalHandler);

function closeModalHandler(event) {
    if (event) {
        event.preventDefault(); // Чтобы избежать дублирования события
    }
    modal.style.display = 'none';
    if (activeModals) {
        activeModals.forEach((modal, id) => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
            activeModals.delete(id);
        });
    }
}

function showModal(title, content, callback = null) {
    if (activeModals) {
        activeModals.forEach((modal, id) => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
            activeModals.delete(id);
        });
    }
    modalTitle.innerHTML = title;
    modalContent.innerHTML = content;
    modal.style.display = 'flex';

    if (document.querySelectorAll('.reward-icon').length > 0) {
        document.querySelectorAll('.reward-icon').forEach(icon => {
            icon.addEventListener('click', event => {
                const item = JSON.parse(event.target.getAttribute('data-item'));

                if (item && !activeModals.has(item.id)) {
                    // Получаем координаты и размеры элемента
                    const rect = event.target.getBoundingClientRect();
                    openItemModal(item, rect.left, rect.top);
                    if (document.querySelectorAll('[data-item-action-equip]')) {
                        document.querySelectorAll('[data-item-action-equip]').forEach(equip => {
                            equip.onclick = async (e) => {
                                e.preventDefault();
                                let user_item_id = e.target.closest('.modal-item').getAttribute('data-id');
                                await websocketRequest(`/player`, {'action': 'item_equip', 'user_item_id': user_item_id}).then(async response => {
                                    if (response?.equipped === true) {
                                        //сделаем запрос и получим новые данные персонажа
                                        Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
                                        localStorage.setItem('user_info', JSON.stringify(Variable.getSelfInfo()));
                                        //перерисуем модалку
                                        showModal(Variable.getSelfInfo().name, Utils.drawCharacterWindows(Variable.getSelfInfo()));
                                        Utils.updateStatusBar(Variable.getSelfInfo());
                                    }
                                });
                            };
                        });
                    }
                    if (document.querySelectorAll('[data-item-action-destroy]')) {
                        document.querySelectorAll('[data-item-action-destroy]').forEach(destroy => {
                            destroy.onclick = async (e) => {
                                e.preventDefault();
                                openConfirmModal(async (count) => {
                                    let user_item_id = e.target.closest('.modal-item').getAttribute('data-id');
                                    await websocketRequest(`/player`, {'action': 'user_item_delete', 'user_item_id': user_item_id, 'count': count});
                                    //сделаем запрос и получим новые данные персонажа
                                    Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
                                    //localStorage.setItem('user_info', JSON.stringify(Variable.getSelfInfo()));
                                    //перерисуем модалку
                                    showModal(Variable.getSelfInfo().name, Utils.drawCharacterWindows(Variable.getSelfInfo()));
                                    Utils.updateStatusBar(Variable.getSelfInfo());
                                }, item.quantity);
                            };
                        });
                    }
                }
            });
        });
    }
    Utils.observeNewImages();
    makeDraggable(modal);
    if (callback && typeof callback === 'function') {
        callback();
    }
}

// Функция для открытия модального окна
// Функция для открытия модального окна
function openConfirmModal(onConfirm, maxQuantity = 0) {
    const confirmModal = document.querySelector("#confirm-modal");
    const cancelDelete = document.querySelector("#modal-cancel-btn");
    const confirmDelete = document.querySelector("#modal-confirm-btn");
    const decrementBtn = document.getElementById("decrement-btn");
    const incrementBtn = document.getElementById("increment-btn");
    const quantityInput = document.getElementById("quantity-input");

    quantityInput.value = 1;
    quantityInput.max = maxQuantity;

    if (maxQuantity) {
        document.querySelector('.quantity-selector').style.display = 'block';
    }

    confirmModal.style.display = "block";

    decrementBtn.onclick = () => {
        const currentValue = parseInt(quantityInput.value, 10);
        if (currentValue > parseInt(quantityInput.min, 10)) {
            quantityInput.value = currentValue - 1;
        }
    };

    incrementBtn.onclick = () => {
        const currentValue = parseInt(quantityInput.value, 10);
        if (currentValue < parseInt(quantityInput.max, 10)) {
            quantityInput.value = currentValue + 1;
        }
    };

    cancelDelete.onclick = () => {
        confirmModal.style.display = "none";
    };

    confirmDelete.onclick = () => {
        confirmModal.style.display = "none";
        if (onConfirm) onConfirm(parseInt(quantityInput.value, 10));
    };
    makeDraggable(confirmModal);
}

// Модалка для предметов
let zIndexCounter = 100; // Track z-index for modal layering

function openItemModal(item, x, y) {
    const modal = document.createElement('div');
    modal.classList.add('modal-item');

    // Учитываем размеры модалки и padding
    const modalWidth = 250 + 20; // ширина + padding
    const modalHeight = 250 + 20; // высота + padding
    const offset = 10; // дополнительное смещение для визуальной разрядки

    // Начальные координаты
    let left = x + offset;
    let top = y + offset;

    // Проверяем, не выходит ли модалка за экран (учитываем padding)
    if (left + modalWidth > window.innerWidth) {
        left = window.innerWidth - modalWidth - offset;
    }
    if (top + modalHeight > window.innerHeight) {
        top = window.innerHeight - modalHeight - offset;
    }

    // Убедимся, что не уходим влево или вверх
    left = Math.max(0, left);
    top = Math.max(0, top);

    modal.style.left = `${left}px`;
    modal.style.top = `${top}px`;
    modal.style.zIndex = ++zIndexCounter;

    modal.setAttribute('data-id', (item.user_item_id) ? item.user_item_id : 0);
    let show_button_block = (item.user_item_id) ? 'flex' : 'none'
    modal.innerHTML = Utils.drawItemInfo(item, show_button_block);

    document.body.appendChild(modal);
    activeModals.set((item.user_item_id) ? item.user_item_id : item.item_id, modal);

    // Функционал закрытия модалки
    modal.querySelector('.modal-close').addEventListener('click', () => {
        document.body.removeChild(modal);
        activeModals.delete(item.id);
    });
    modal.querySelector('.modal-close').addEventListener('touchend', () => {
        document.body.removeChild(modal);
        activeModals.delete(item.id);
    });

    // Перемещение модалки на передний план
    modal.addEventListener('mousedown', () => {
        modal.style.zIndex = ++zIndexCounter;
    });

    makeDraggable(modal);
}

function makeDraggable(element) {
    let offsetX = 0, offsetY = 0, isDragging = false, initialX, initialY;
    const modalHeader = element.querySelector('.modal-header');

    // Универсальная функция для получения координат
    const getCoordinates = (e) => {
        if (e.touches && e.touches.length > 0) {
            return {x: e.touches[0].clientX, y: e.touches[0].clientY};
        }
        return {x: e.clientX, y: e.clientY};
    };

    // Функция корректировки позиции
    const adjustPosition = () => {
        const rect = element.getBoundingClientRect();
        let newLeft = rect.left;
        let newTop = rect.top;

        if (rect.right > window.innerWidth) {
            newLeft = window.innerWidth - rect.width;
        }
        if (rect.left < 0) {
            newLeft = 0;
        }
        if (rect.bottom > window.innerHeight) {
            newTop = window.innerHeight - rect.height;
        }
        if (rect.top < 0) {
            newTop = 0;
        }

        element.style.left = `${newLeft}px`;
        element.style.top = `${newTop}px`;
    };

    // Начало перетаскивания (десктоп и мобилки)
    const startDrag = (e) => {
        if (e.target.id === 'closeModal') return; // Игнорируем клик по кнопке
        e.preventDefault();
        const {x, y} = getCoordinates(e);
        initialX = x;
        initialY = y;
        isDragging = true;
        offsetX = element.offsetLeft;
        offsetY = element.offsetTop;
        modalHeader.style.cursor = 'grabbing';
    };

    // Завершение перетаскивания
    const endDrag = () => {
        isDragging = false;
        modalHeader.style.cursor = 'grab';
    };

    // Перемещение модального окна
    const moveDrag = (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const {x, y} = getCoordinates(e);
        const dx = x - initialX;
        const dy = y - initialY;
        const newLeft = Math.min(window.innerWidth - element.offsetWidth, Math.max(0, offsetX + dx));
        const newTop = Math.min(window.innerHeight - element.offsetHeight, Math.max(0, offsetY + dy));

        element.style.left = `${newLeft}px`;
        element.style.top = `${newTop}px`;
        element.style.transform = 'none'; // Отключаем центрирование через transform
    };

    // События для мыши
    modalHeader.addEventListener('mousedown', startDrag);
    document.addEventListener('mouseup', endDrag);
    document.addEventListener('mousemove', moveDrag);

    // События для сенсорных экранов
    modalHeader.addEventListener('touchstart', startDrag, {passive: false});
    document.addEventListener('touchend', endDrag, {passive: false});
    document.addEventListener('touchmove', moveDrag, {passive: false});

    // Корректировка позиции при инициализации
    adjustPosition();
    //дополнительно проверяем на ресайз и смещаем модалку при необходимости
    window.addEventListener('resize', adjustPosition);
}

const Modal = {
    modalTitle,
    modalContent,
    modal,
    showModal,
    closeModalHandler,
    openConfirmModal
};

export default Modal;