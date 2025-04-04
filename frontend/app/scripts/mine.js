import Variable from "./variable";
import {websocketRequest} from "./websocket";
import Utils from "./utils";
import Modal from "./modal";

export async function animatedMine(object_id, mine_time, event) {
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
            console.log('Действие завершено!');

            // По окончанию анимации мы отправим запрос и проверим успешность и получим лут
            const responseMined = await websocketRequest(`/resource`, {'action': 'check_mine', 'resource_id': object_id});
            if (responseMined.reward && responseMined.reward.length > 0) {
                let text = 'Вы получили:<br>'
                responseMined.reward.forEach(item => {
                    text += `${item.name} x${item.quantity}<br>`;
                })
                //сделаем запрос и получим новые данные персонажа
                Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
                //localStorage.setItem('user_info', JSON.stringify(Variable.getSelfInfo()));
                Utils.createToast(text);
                Modal.closeModalHandler(event)
            }
        }
    }, 100);
}
