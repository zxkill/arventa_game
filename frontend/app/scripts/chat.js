import '../css/chat.css'
import {websocketRequest} from "./websocket";

function drawMessages(messages) {
    let messageStr = '';
    if (messages && messages.length > 0) {
        messages.forEach(message => {
            let date = new Date(message.timestamp);
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            const formattedTime = `${hours}:${minutes}`;
            messageStr += `
                <div class="chat-message">
                  <p class="chat-user"><b data-user-id="${message.user_id}">${message.user_name}</b> | ${formattedTime}: <span>${message.message}</span></p>
                </div>
            `;
        })
    } else {
        messageStr = 'Тут пока пусто';
    }

    return messageStr;
}

function drawChat(messages) {
    return `
        <div id="chat" class="chat-container">
          <div id="chat-header" class="chat-header">
            <span id="chat-toggle" class="chat-toggle">&#128172;</span>
          </div>
          <div id="chat-body" class="chat-body">
            ${drawMessages(messages)}
          </div>
          <div id="chat-input" class="chat-input">
            <input type="text" id="message" placeholder="Введите сообщение..." />
          </div>
        </div>
    `;
}

async function chat(init = false, messages = []) {
    if (init) {
        //запросим сообщения
        await websocketRequest('/chat', {'action': 'get_messages'}).then(async response => {
            let messages = [];
            if (response && response.messages && response.messages.length > 0) {
                messages = response.messages;
            }
            document.querySelector('body').insertAdjacentHTML('beforeend', drawChat(messages));
            events();
        }).catch(error => {
            console.log(error.message);
        });
    } else {
        document.querySelector('.chat-body').innerHTML = drawMessages(messages);
        document.querySelector('.chat-body').scrollTop = document.querySelector('.chat-body').scrollHeight;
    }
}

function events() {
    const chatHeader = document.getElementById('chat-header');
    const chatContainer = document.getElementById('chat');
    const messageInput = document.getElementById('message');
    chatHeader.addEventListener('click', function () {
        chatContainer.classList.toggle('active');
        if (!chatContainer.classList.contains('active')) {
            messageInput.blur();
        } else {
            document.querySelector('.chat-body').scrollTop = document.querySelector('.chat-body').scrollHeight;
            messageInput.focus();
        }
    });

    messageInput.addEventListener('focus', function () {
        chatContainer.style.opacity = '1';
    });

    messageInput.addEventListener('blur', function () {
        setTimeout(() => {
            if (document.activeElement !== chatContainer) {
                chatContainer.style.opacity = '0.5';
            }
        }, 100);
    });

    messageInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter' || event.keyCode === 13) {
            event.preventDefault();
            if (await sendMessage(event.target.value.trim())) {
                event.target.value = '';
            }
        }
    });
    document.querySelector('.chat-body').scrollTop = document.querySelector('.chat-body').scrollHeight;
    return true;
}

// Функция отправки сообщения
async function sendMessage(messageText) {
    if (messageText === '') return;

    await websocketRequest('/chat', {'action': 'send', 'message': messageText}).then(async response => {
        if (response && response.send === true) {

        }
    });

    // Прокручиваем чат вниз
    document.querySelector('.chat-body').scrollTop = document.querySelector('.chat-body').scrollHeight;
    return true;
}

const Chat = {
    chat
}

export default Chat;