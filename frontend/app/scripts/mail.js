import '../css/mail.css'
import {websocketRequest} from "./websocket";
import Modal from "./modal";
import Utils from "./utils";
import Variable from "./variable";

async function getMail() {
    let listString = '';

    if (!Variable.getUserMails() || Variable.getUserMails()?.length <= 0) {
        await websocketRequest('/mail', {'action': 'get_messages'}).then(messages => {
            Variable.setUserMails(messages);
            updateCountMail(Variable.getUserMails());
        }).catch(error => {
            console.log(error);
        });
    }

    const messages = Variable.getUserMails();
    messages.forEach(message => {
        let date = new Date(message.datetime);
        const year = date.getFullYear().toString();
        const month = date.getMonth().toString().padStart(2, '0');
        const day = date.getDay().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const formattedTime = `${day}.${month}.${year} ${hours}:${minutes}`;
        listString += `
            <div class="mail-item${(message.is_read === false) ? ' unread' : ''}" data-id="${message.id}">
                <span>${message.subject}</span>
                <span>${formattedTime}</span>
            </div>
            <div class="mail-content" id="mail-${message.id}" style="display: none;">
                <span><strong>От:</strong> ${message.sender_name}</span>
                <h3>${message.subject}</h3>
                <p>${message.message}</p>
                <div class="mail-button"> 
                    <button class="btn close-mail" data-id="${message.id}">Закрыть</button>
                    <button class="btn delete-mail" data-id="${message.id}">Удалить</button>
                </div>
            </div>
        `;
    });


    Modal.showModal('Почта', `
        <div class="mail-container">
            <div class="mail-list">
                ${(listString) ? listString : 'Писем пока нет'}
            </div>
            <div class="mail-compose" id="compose-mail" style="display: none;">
                <h3>Написать письмо</h3>
                <div class="recipient-wrapper" style="position: relative;">
                    <input class="input-field" autocomplete="off" type="text" placeholder="Получатель (никнейм)" id="recipient">
                    <div id="recipient-suggestions" class="suggestions"></div>
                </div>
                <input class="input-field" type="text" placeholder="Тема" id="subject">
                <textarea class="input-field" placeholder="Сообщение" id="message"></textarea>
                <div class="mail-button"> 
                    <button class="btn" id="send-mail">Отправить</button>
                    <button class="btn" id="close-compose">Отмена</button>
                </div>
            </div>
            <div class="mail-footer">
                <button class="btn" id="open-compose">Написать письмо</button>
            </div>
        </div>
    `, loadEvents);
}

const loadEvents = () => {
    // Привязываем события для автоподстановки при вводе в поле получателя
    const recipientInput = document.getElementById('recipient');
    const suggestion = document.getElementById('recipient-suggestions');
    let recipientSearchTimeout;
    recipientInput.addEventListener('input', function (e) {
        clearTimeout(recipientSearchTimeout);
        const query = e.target.value.trim();
        // Если введено меньше 2 символов — очищаем подсказки
        if (query.length < 2) {
            suggestion.innerHTML = '';
            suggestion.style.display = 'none';
            recipientInput.removeAttribute('data-id');
            return;
        }
        // Задержка перед поиском (debounce)
        recipientSearchTimeout = setTimeout(async () => {
            await websocketRequest('/player', {'action': 'find_users', 'query': query}).then(users => {
                let suggestions = '';
                users.forEach(user => {
                    suggestions += `<div class="suggestion" data-id="${user.id}" style="padding: 5px; cursor: pointer;">${user.username}</div>`;
                });
                suggestion.innerHTML = suggestions;
                suggestion.style.display = 'flex';
                // Навешиваем обработчик на каждый вариант
                document.querySelectorAll('#recipient-suggestions .suggestion').forEach(elem => {
                    elem.addEventListener('click', function () {
                        recipientInput.value = this.textContent;
                        recipientInput.setAttribute('data-id', this.getAttribute('data-id'));
                        suggestion.innerHTML = '';
                        suggestion.style.display = 'none';
                    });
                });
            }).catch(error => {
                console.log(error);
            });
        }, 300);
    });

    document.querySelectorAll('.mail-item').forEach(item => {
        item.addEventListener('click', (e) => openMail(item.dataset.id, item));
    });

    document.querySelectorAll('.close-mail').forEach(button => {
        button.addEventListener('click', () => closeMail(button.dataset.id));
    });
    document.querySelectorAll('.delete-mail').forEach(button => {
        button.addEventListener('click', () => deleteMail(button.dataset.id));
    });

    document.getElementById('open-compose').addEventListener('click', openCompose);
    document.getElementById('close-compose').addEventListener('click', closeCompose);
    document.getElementById('send-mail').addEventListener('click', sendMail);
};

async function openMail(id, element) {
    document.querySelectorAll('.mail-content').forEach(el => el.style.display = 'none');
    document.getElementById('mail-' + id).style.display = 'block';
    if (element.classList.contains('unread')) {
        element.classList.remove('unread'); // Убираем статус непрочитанного
        await websocketRequest('/mail', {'action': 'read', 'mail_id': id}).then(response => {
            if (response?.read === true) {
                let newMail = [];
                Variable.getUserMails().forEach(mail => {
                    if (mail.id === parseInt(id)) {
                        mail.is_read = true;
                    }
                    newMail.push(mail);
                });
                Variable.setUserMails(newMail);
                updateCountMail(newMail);
            }
        }).catch(error => {
            console.log(error);
        });
    }
}

function closeMail(id) {
    document.getElementById('mail-' + id).style.display = 'none';
}

async function deleteMail(id) {
    await websocketRequest('/mail', {'action': 'delete', 'mail_id': id}).then(response => {
        if (response?.deleted && response?.deleted === true) {
            const mailContent = document.getElementById('mail-' + id);
            const mailItem = document.querySelector('.mail-item[data-id="' + id + '"]');

            if (mailContent) {
                mailContent.classList.add('fade-out');
            }
            if (mailItem) {
                mailItem.classList.add('fade-out');
            }

            setTimeout(() => {
                if (mailContent) mailContent.remove();
                if (mailItem) mailItem.remove();
            }, 300);
        }
    }).catch(error => {
        console.log(error);
    });
}

function openCompose() {
    document.getElementById('compose-mail').style.display = 'block';
}

function closeCompose() {
    document.getElementById('compose-mail').style.display = 'none';
}

async function sendMail() {
    const recipientInput = document.getElementById('recipient');
    // Берём ID из data-атрибута
    const recipient_id = recipientInput.getAttribute('data-id');
    const subject = document.getElementById('subject').value.trim();
    const message = document.getElementById('message').value.trim();

    if (!recipient_id || !subject || !message) {
        Utils.createToast('Все поля обязательны для заполнения!');
        return;
    }
    if (subject.length > 100) {
        Utils.createToast('Тема письма не должна превышать 100 символов!');
        return;
    }
    if (message.length > 1000) {
        Utils.createToast('Сообщение не должно превышать 1000 символов!');
        return;
    }

    await websocketRequest('/mail', {'action': 'send', recipient_id, subject, message}).then(response => {
        closeCompose();
        document.getElementById('subject').value = '';
        document.getElementById('message').value = '';
        recipientInput.value = '';
    }).catch(error => {
        console.log(error);
    });
}

function updateCountMail(mails) {
    let count = 0;
    if (mails && mails) {
        mails.forEach(mail => {
            if (mail.is_read === false) {
                count++;
            }
        })
        const notifyBadge = document.querySelector('.notification-badge-mail');
        if (count > 0) {
            notifyBadge.innerText = count;
            notifyBadge.style.display = 'block';
        } else {
            notifyBadge.style.display = 'none';
        }
    }
}

const Mail = {
    getMail,
    updateCountMail
}

export default Mail;
