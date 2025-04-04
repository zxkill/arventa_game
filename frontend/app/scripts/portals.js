import '../css/portal.css'
import {websocketRequest} from "./websocket";
import Modal from "./modal";
import Variable from "./variable";

export async function getPortalInfo(object_id) {
    await websocketRequest(`/portal`, {'action': 'get_portal', 'portal_id': object_id}).then(portalInfo => {
        // Отображаем информацию во всплывающем окне
        if (portalInfo) {
            Modal.showModal(portalInfo?.name, `
                        <p>${portalInfo?.description}</p>
                        <p>Для закрытия этого разлома необходимо <b>${portalInfo.energy_required} Энергии Арвенты</b>, но сперва нужно будет <b>ввести верный код</b>. Приготовьтесь.</p>
                        <button class="portal-close">Закрыть разлом</button>
                    `);
            if (document.querySelector('.portal-close')) {
                document.querySelector('.portal-close').onclick = (async (event) => {
                    event.preventDefault();
                    event.target.disabled = true;
                    Modal.showModal(portalInfo?.name, `
                        <div class="portal-window">
                            <div id="instruction">
                                Запомните последовательность символов, которая появится на секунду.<br>
                                Затем повторите её, нажимая на символы из набора за 10 секунд.
                            </div>
                            <div id="selectedContainer"></div>
                            <div id="glyphContainer" style="display: none;"></div>
                            <div id="buttons">
                                <button id="resetButton">Сбросить</button>
                            </div>
                            <div id="timer"></div>
                            <div id="message"></div>
                            <div id="overlay" style="display: none;"></div>
                          </div>
                    `);
                    await loadPuzzle(object_id);
                });
            }
        }
    });
}

// Переменные для хранения данных пазла
let targetSequence = "";
let options = [];
let puzzleId = null; // идентификатор пазла (мок)
let selectedSequence = "";
let countdownTimer = null;
const TOTAL_TIME = 10; // 10 секунд на ввод

// Элементы интерфейса
let instructionEl;
let glyphContainer;
let selectedContainer;
let resetButton;
let messageEl;
let timerEl;
let overlayEl;

// Функция запуска обратного отсчёта (10 секунд)
function startCountdown() {
    let timeLeft = TOTAL_TIME;
    timerEl.textContent = `Осталось времени: ${timeLeft} с`;
    countdownTimer = setInterval(() => {
        timeLeft--;
        timerEl.textContent = `Осталось времени: ${timeLeft} с`;
        if (timeLeft <= 0) {
            clearInterval(countdownTimer);
            timerEl.textContent = "Время истекло!";
            messageEl.textContent = "Время вышло! Разлом остаётся открытым.";
            // Сбросим выбор через короткую паузу
            setTimeout(resetSelection, 1500);
        }
    }, 1000);
}

// Функция загрузки пазла (мок)
async function loadPuzzle(object_id) {
    // Элементы интерфейса
    instructionEl = document.getElementById("instruction");
    glyphContainer = document.getElementById("glyphContainer");
    selectedContainer = document.getElementById("selectedContainer");
    resetButton = document.getElementById("resetButton");
    messageEl = document.getElementById("message");
    timerEl = document.getElementById("timer");
    overlayEl = document.getElementById("overlay");
    // Привязка событий к кнопкам
    resetButton.addEventListener("click", resetSelection);
    await websocketRequest(`/portal`, {
        'action': 'get_puzzle',
        'portal_id': object_id
    }).then(response => {
        puzzleId = response.puzzle_id;
        targetSequence = response.sequence;
        options = response.options;

        // Перед началом игры показываем цель (последовательность символов) на 1 секунду в оверлее
        overlayEl.style.display = "flex";
        overlayEl.textContent = targetSequence;
        // Скрываем контейнер выбора символов, чтобы игрок не мог подсмотреть
        glyphContainer.style.display = "none";
        selectedSequence = "";
        selectedContainer.innerHTML = "";
        messageEl.textContent = "";
        timerEl.textContent = "";

        // Через 1 секунду скрываем оверлей и показываем опции
        setTimeout(() => {
            overlayEl.style.display = "none";
            overlayEl.textContent = '';
            glyphContainer.style.display = "flex";
            // Перемешиваем опции
            glyphContainer.innerHTML = "";
            const shuffled = options.slice().sort(() => Math.random() - 0.5);
            shuffled.forEach(symbol => {
                const btn = document.createElement("div");
                btn.classList.add("glyph");
                btn.textContent = symbol;
                btn.addEventListener("click", () => selectSymbol(symbol));
                glyphContainer.appendChild(btn);
            });
            // Запускаем обратный отсчёт 10 секунд для ввода последовательности
            startCountdown();
        }, 1000);
    }).catch(error => {
        instructionEl.textContent = "Не удалось загрузить пазл.";
        console.error(error);
    });
}

// Функция выбора символа игроком
function selectSymbol(symbol) {
    if (selectedSequence.length < targetSequence.length) {
        selectedSequence += symbol;
        const span = document.createElement("div");
        span.classList.add("glyph");
        span.textContent = symbol;
        selectedContainer.appendChild(span);
        if (selectedSequence.length === targetSequence.length) {
            setTimeout(submitSequence, 300);
        }
    }
}

// Функция сброса выбранной последовательности
function resetSelection() {
    selectedSequence = "";
    selectedContainer.innerHTML = "";
    messageEl.textContent = "";
    clearInterval(countdownTimer);
    timerEl.textContent = "";
    loadPuzzle().then(r => {
    });
}

// Функция отправки выбранной последовательности на проверку
async function submitSequence() {
    clearInterval(countdownTimer);
    messageEl.textContent = "Проверка...";
    await websocketRequest(`/portal`, {
        'action': 'check_puzzle',
        'puzzle_id': puzzleId,
        'selected_sequence': selectedSequence
    }).then(async response => {
        if (response?.closed === true) {
            //обновляем инвентарь игрока
            Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
        }
    }).catch(error => {
        messageEl.textContent = "Ошибка связи с сервером.";
        console.error(error);
    }).finally(() => {
        Modal.closeModalHandler();
    })
}

async function getStats() {
    let rows = '';
    await websocketRequest(`/portal`, {'action': 'get_stats'}).then(stats => {
        if (stats) {
            stats?.forEach(player => {
                rows += `
                    <tr>
                      <td>${player.position}</td>
                      <td>${player.username}</td>
                      <td>${player.total_attempts}</td>
                      <td>${player.total_points}</td>
                      <td>${player.avg_closure_time}</td>
                      <td>${player.total_energy_used}</td>
                    </tr>
                `;
            })
        }
    });
    return `
        <div class="table-container rpg-border">
        <table class="statistics-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Игрок</th>
              <th>Разломов закрыто</th>
              <th>Очки</th>
              <th>Ср. время</th>
              <th>Энергия потрачена</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
}

const Portal = {
    getStats
}

export default Portal;
