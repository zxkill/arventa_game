import '../css/crafting.css'
import Utils from "./utils";
import {websocketRequest} from "./websocket";
import Variable from "./variable";

function drawCraftingWindow(receipts) {
    return `
        <div class="crafting-window">
            <div class="crafting-buttons">
                <button class="craft-button active" data-item-type='resource'>Ресурсы</button>
                <button class="craft-button" data-item-type='weapon'>Оружие</button>
                <button class="craft-button" data-item-type='armor'>Броня</button>
                <button class="craft-button" data-item-type='tool'>Инструменты</button>
            </div>

            <div class="recipe-list">
                ${drawReceipt(receipts)}
            </div>
        </div>
    `;
}

function drawReceipt(receipts) {
    let recipeStr = '';
    let required = '';
    if (receipts && Object.keys(receipts).length > 0) {
        receipts.forEach(recipe => {
            required = '';
            let item_not_allowed = false;
            recipe.materials_required.forEach(material => {
                required += `${material.count} ${material.resource.name}<br>`;
            });
            Variable.getSelfInfo()?.skill_progress.forEach(progress => {
            if ((recipe.item.type === progress.type_item) && (recipe.item.resource_type === progress.type_resource) && (recipe.item.tier > progress.current_level)) {
                item_not_allowed = true;
            } else if ((recipe.item.type === 'resource') && (progress.type_item === 'craft') && (recipe.item.resource_type === progress.type_resource) && (recipe.item.tier > progress.current_level)) {
                item_not_allowed = true;
            }
        })
            recipeStr += `
                <div class="recipe-item" style="display: ${(recipe.item.type === 'resource' ? 'flex' : 'none')}" data-item-type="${recipe.item.type}">
                    ${Utils.drawItem(recipe.item)}
                    <div class="recipe-info">
                        <h3>${recipe.item.name}</h3>
                        <p>${required}</p>
                    </div>
                    <button class="craft-btn" ${(item_not_allowed) ? 'disabled' : ''} data-craft-run="${recipe.id}">Изготовить</button>
                </div>
            `;
        });
        return recipeStr;
    } else {
        return `Рецепты отсутствуют`;
    }
}

async function animatedCraft(recipe_id, mine_time, event) {
    // Создаем прогресс-бар, если его нет
    let progressBar = document.querySelector('.progress-bar');
    if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.classList.add('progress-bar');
        progressBar.style.position = 'relative';
        progressBar.style.width = '100%';
        progressBar.style.backgroundColor = '#fff';
        progressBar.style.borderRadius = '4px';
        progressBar.style.height = '10px';

        const progressFill = document.createElement('div');
        progressFill.classList.add('progress-fill');
        progressFill.style.width = '0%';
        progressFill.style.height = '10px';
        progressFill.style.borderRadius = '4px';
        progressFill.style.backgroundColor = '#249702';
        progressBar.appendChild(progressFill);

        document.querySelector('#modal-content').appendChild(progressBar);
    }

    const progressFill = progressBar.querySelector('.progress-fill');

    // Таймер
    let elapsedSeconds = 0;
    mine_time = mine_time * 10;
    const timerInterval = setInterval(async () => {
        elapsedSeconds++;
        const progressPercentage = (elapsedSeconds / mine_time) * 100;

        progressFill.style.width = `${progressPercentage}%`;

        if (elapsedSeconds >= mine_time) {
            clearInterval(timerInterval);
            progressFill.style.width = '100%';
            event.target.disabled = false;
            // По окончанию анимации мы отправим запрос и проверим успешность
            await websocketRequest(`/recipe`, {'action': 'get_make_result', 'recipe_id': recipe_id}).then(async response => {
                //сделаем запрос и получим новые данные персонажа
                Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
                //localStorage.setItem('user_info', JSON.stringify(Variable.getSelfInfo()));
            });
        }
    }, 100);
}


const DrawCrafting = {
    drawCraftingWindow,
    animatedCraft
}

export default DrawCrafting;
