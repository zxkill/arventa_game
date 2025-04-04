import Utils from "./utils";

function updateCountQuest(userQuests) {
    if (userQuests && userQuests.length) {
        const notifyBadge = document.querySelector('.notification-badge');
        notifyBadge.innerText = userQuests.length;
        notifyBadge.style.display = 'block';
    }
}

/**
 *
 * @param quests
 * @param type - view or accept
 * @returns {string}
 */
function generateQuestWindow(quests, type = 'view') {
    let content = '';
    let reward = '';
    let items = '';
    let goals = '';
    let button = '';
    let silver = '';
    if (quests && quests.length) {
        let i = 1;
        quests.forEach(quest => {
            reward = ``;
            items = ``;
            goals = ``;
            button = ``;
            silver = '';
            //сформируем блок наград
            if (Object.keys(quest.reward).length > 0) {
                if (quest.reward.items) {
                    quest.reward.items.forEach(item => {
                        items += Utils.drawItem(item);
                    });
                }
                if (quest.reward.money) {
                    if (quest.reward.money.silver > 0) {
                        silver = `
                            <div class="reward-stats">
                            <div class="reward-money">
                              <span class="silver-amount" title="Серебро">${quest.reward.money.silver}</span>
                            </div>
                          </div>
                        `;
                    }
                }
                //<span class="gold-amount" title="Золото">${quest.reward.money.gold}</span>
                reward += `
                        <div class="quest-rewards">
                          <b>Награда</b>
                          <div class="reward-items">
                            ${items}
                          </div>
                          ${silver}
                        </div>
                    `;
            }
            if (quest.conditions) {
                items = ``;
                quest.conditions.forEach(condition => {
                    items += `
                            <div>${condition.action}: ${(condition.target_name) ? condition.target_name + ' - ' : ''}  ${(condition.current) ? condition.current : 0}/${condition.quantity}</div>
                        `;
                });
                if (items.length > 0) {
                    goals += `
                            <div class="quest-conditions">
                              <b>Цели</b>
                              <div class="condition-items">
                                ${items}
                              </div>
                            </div>
                        `;
                }
            }
            if (type === 'accept') {
                button = `<button class="button-access" data-quest-id="${quest.id}">Принять квест</button>`;
            } else if (type === 'view' && quest.completed) {
                button = `<button class="complete-quest-button" data-quest-id="${quest.id}">Завершить</button>`;
            } else if (type === 'view') {
                //button = `<button class="cancel-quest-button" data-quest-id="${quest.id}">Отменить</button>`;
            }
            content += `
                    <div class="row" data-row-questId="${quest.id}" onclick="return false;">
                        <div class="collapsible-header" data-open-content><b>${i}. ${quest.name}</b></div>
                        <div class="collapsible-content">
                            <p>${quest.description}</p>
                            ${goals}
                            ${reward}
                            ${button}
                        </div>
                    </div>
                `;
            i++;
        });
    } else {
        content = `<div class="quest-empty">Тут пока пусто</div>`;
    }
    return `<div class="quest-list">${content}</div>`;
}

const Quest = {
    generateQuestWindow,
    updateCountQuest
};

export default Quest;
