import '../css/player-info.css'
import {websocketRequest} from "./websocket";


async function drawPlayerWindow(object_id) {
    let info = '';
    // Получаем информацию о точке с бэкенда
    await websocketRequest(`/player`, {
        'action': 'get_player_info',
        'player_id': object_id
    }).then(playerInfo => {
        info = `
            <div class="player-info">
                <div class="top-section">
                    <div class="avatar">
                        <img src="${playerInfo.avatar}" alt="">
                    </div>
                    <div class="details">
                        ${playerInfo.username}
                        <br>
                        <b>Дата регистрации:</b> ${playerInfo.register}
                    </div>
                </div>
                <div class="info">
                    ${(playerInfo.name) ? '<b>Имя:</b> ' + playerInfo.name : ''}<br>
                    ${(playerInfo.birthday) ? '<b>Дата рождения:</b> ' + playerInfo.birthday : ''}<br>
                    ${(playerInfo.bio) ? '<b>Немного о себе:</b> ' + playerInfo.bio : ''}<br>
                </div>
            </div>
        `;
    });
    return info;
}

const PlayerWindow = {
    drawPlayerWindow,
}

export default PlayerWindow;