import '../css/profile.css'
import {websocketRequest} from "./websocket";
import Modal from "./modal";
import Variable from "./variable";
import Utils from "./utils";


function drawProfileWindow() {
    const profile = Variable.getSelfInfo().profile;
    return `
        <form id="profile-form">
          <div class="profile-row">
            <div class="profile-avatar">
                <label for="avatar">Аватар:</label>
                <img id="current-avatar" data-avatar-id="${profile.avatar_id}" src="${profile.avatar}" alt="">
                <button type="button" id="change-avatar-btn">Изменить</button>
            </div>
          </div>
          <div class="avatar-selection" id="avatar-selection" style="display: none;"></div>
          <div class="profile-row">
            <div>
              <label for="username">Имя:</label>
              <input type="text" name="name" placeholder="Иван" value="${profile.name}">
            </div>
            <div>
              <label for="birthday">Дата рождения:</label>
              <input type="date" name="birthday" value="${profile.birthday}">
            </div>
          </div>
          <label for="description">Немного о себе:</label>
          <textarea name="bio" placeholder="Расскажите немного о себе. Как часто вы играете, какой тип игры предпочитаете...">${profile.bio}</textarea>

          <div class="buttons">
            <button type="button" id="save-btn">Сохранить</button>
          </div>
        </form>
    `;
}

function events() {
    // Обработка кнопок
    document.querySelector('#save-btn').addEventListener('click', async function (e) {
        e.preventDefault();
        const name = document.querySelector('input[name="name"]').value;
        const bio = document.querySelector('textarea[name="bio"]').value;
        const birthday = document.querySelector('input[name="birthday"]').value;
        const avatar_id = document.querySelector('#current-avatar').getAttribute('data-avatar-id');
        /*if (!name || !bio || !birthday) {
            Utils.createToast('Все поля обязательны для заполнения');
            return;
        }*/
        await websocketRequest('/profile', {
            'action': 'save',
            'name': name,
            'bio': bio,
            'birthday': birthday,
            'avatar_id': avatar_id,
        }).then(async (response) => {
            if (response && response.saved === true) {
                Modal.closeModalHandler(e);
                Variable.setSelfInfo(await websocketRequest('/player', {'action': 'get_self'}));
                Utils.updateStatusBar(Variable.getSelfInfo());
                console.log(Variable.getSelfInfo());
            }
        });
        return false;
    });
    const changeAvatarBtn = document.querySelector('#change-avatar-btn');
    const avatarSelection = document.querySelector('#avatar-selection');
    const currentAvatarImg = document.querySelector('#current-avatar');

    // Показать или скрыть блок с аватарами
    changeAvatarBtn.addEventListener('click', async function () {
        await websocketRequest('/avatar', {'action': 'get'}).then(async (response) => {
            let avatarStr = '';
            if (response && response.length > 0) {
                response.forEach((avatar) => {
                    avatarStr += `<img src="${avatar.url}" data-avatar-id="${avatar.id}" class="avatar-option" data-avatar="${avatar.url}" alt="${avatar.title}">`;
                });
            }
            avatarSelection.innerHTML = avatarStr;
            // Обновить текущий аватар при выборе
            document.querySelectorAll('.avatar-option').forEach(function (img) {
                img.addEventListener('click', function () {
                    currentAvatarImg.src = img.getAttribute('data-avatar');
                    currentAvatarImg.setAttribute('data-avatar-id', img.getAttribute('data-avatar-id'));
                    avatarSelection.style.display = 'none'; // Скрыть блок после выбора
                });
            });
        });
        avatarSelection.style.display = avatarSelection.style.display === 'none' ? 'flex' : 'none';
    });
    return true;
}

const Profile = {
    drawProfileWindow,
    events
}

export default Profile;