import '../css/progress-bar.css'
import '../css/battle.css'
import Utils from "./utils";
import {websocketRequest} from "./websocket";
import Modal from "./modal";
import Variable from "./variable";

let battleLog;
let buttonAttack;
let monster;

function logMessage(message) {
    const logEntry = document.createElement("p");
    logEntry.innerHTML = message;
    battleLog.appendChild(logEntry);
    battleLog.scrollTop = battleLog.scrollHeight;
}

export async function getMonsterInfo(object_id) {
    await websocketRequest(`/monster`, {'action': 'get', 'monster_id': object_id}).then(monsterInfo => {
        monster = monsterInfo;
        // Отображаем информацию во всплывающем окне
        if (monsterInfo) {
            Modal.showModal(monsterInfo.name, `
                        <p>${monsterInfo.description}</p>
                        <div style="text-align: center;">Здоровье <span id="health-monster">${monster.health}</span> / ${monster.max_health}</div>
                        <div class="progress-bar"><div class="progress-fill" style="width: ${(monster.health * 100) / monster.max_health + '%'}" id="health-monster-progress"></div></div>
                        <button class="monsters-fight">Напасть</button>
                        <div class="battle-log"></div>
                        <button class="monsters-attack" style="display: none">Ударить</button>
                    `);
            battleLog = document.querySelector(".battle-log");
            buttonAttack = document.querySelector('.monsters-attack');
            buttonAttack.onclick = (async (event) => {
                await monsterAttack(object_id, event);
            });
        }
    });

    if (document.querySelector('.monsters-fight')) {
        document.querySelector('.monsters-fight').onclick = (async (event) => {
            event.preventDefault();
            event.target.disabled = true;
            await websocketRequest(`/monster`, {
                'action': 'fight_start',
                'monster_id': object_id
            }).then(async responseAttack => {
                if (responseAttack && responseAttack.fight === true) {
                    await monsterAttack(object_id, event);
                }
            }).catch(error => {
                console.error('Не удалось начать бой: ' + error);
                Utils.createToast('Не удалось начать бой. Попробуйте снова.');
                event.target.disabled = false;
                event.target.style.display = 'block';
            });
        });
    }
}

async function monsterAttack(object_id, event) {
    buttonAttack.setAttribute('disabled', 'disabled');
    //если бой начался, то прячем кнопку начала битвы и делаем первый удар
    await websocketRequest(`/monster`, {
        'action': 'monster_attack',
        'monster_id': object_id
    }).then(async responseAttack => {
        if (!responseAttack) {
            return;
        }
        event.target.style.display = 'none';
        buttonAttack.style.display = 'block';
        // если нанесли урон и бой продолжается
        if (responseAttack.status === 'fight') {
            logMessage(`Вы нанесли врагу ${responseAttack.damage_to_monster} урона.${(responseAttack.damage_to_monster === 0) ? ' Враг уклонился.' : ''}`);
            logMessage(`Враг нанес вам ${responseAttack.damage_to_player} урона.${(responseAttack.damage_to_player === 0) ? ' Вы уклонились.' : ''}`);
            //document.querySelector('.progress-fill').style.width =
        } else if (responseAttack.status === 'victory') { //если победа
            logMessage(`Вы нанесли врагу ${responseAttack.damage_to_monster} урона.`);
            //logMessage(`Враг нанес вам ${responseAttack.damage_to_player} урона.`);
            logMessage("<b>Враг побежден!</b>");
            logMessage("<b>Ваши награды:</b>");
            if (responseAttack.reward.silver) {
                logMessage(`Серебро: ${responseAttack.reward.silver}`);
            }
            if (responseAttack.reward.items.length > 0) {
                responseAttack.reward.items.forEach(item => {
                    logMessage(`${item.name}`)
                })
            }
            buttonAttack.style.display = 'none';
        } else if (responseAttack.status === 'defeat') { //если поражение
            logMessage(`Вы нанесли врагу ${responseAttack.damage_to_monster} урона.${(responseAttack.damage_to_monster === 0) ? ' Враг уклонился.' : ''}`);
            logMessage(`Враг нанес вам ${responseAttack.damage_to_player} урона.`);
            logMessage("Вы проиграли!");
            buttonAttack.style.display = 'none';
        }
        Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
        //localStorage.setItem('user_info', JSON.stringify(Variable.getSelfInfo()));
        Utils.updateStatusBar(Variable.getSelfInfo());

        document.querySelector('#health-monster').textContent = responseAttack.new_health_monster;
        document.querySelector('#health-monster-progress').style.width = '' + (responseAttack.new_health_monster * 100) / monster.max_health + '%';
        buttonAttack.removeAttribute('disabled'); //разблокируем кнопку
    });
}
