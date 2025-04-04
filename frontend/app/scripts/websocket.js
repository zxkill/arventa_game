import Variable from "./variable";
import Utils from "./utils";
import {refreshAccessToken} from "./api";
import Chat from "./chat";
import Mail from "./mail";

let messageQueue = [];
let websocket = null;
let websocketReady = false;
const responseHandlers = {};
const wsUrl = "wss://" + window.location.host + "/ws";

function initializeWebSocket(token) {
    websocket = new WebSocket(`${wsUrl}?token=${token}`);
    websocket.onopen = async () => {
        websocketReady = true;
        console.log("WebSocket connection established");
        let i = 0;
        while (messageQueue.length > 0) {
            websocket.send(messageQueue.shift());
            console.log("WebSocket queue send: " + i);
            i++;
        }
    };

    websocket.onmessage = async (event) => {
        try {
            const response = JSON.parse(event.data);
            console.log("Parsed response:", response); // Логируем распарсенное сообщение
            const {id, action, data, success, message, successMessage} = response;
            console.log(id, action, data, success, message, successMessage);
            if (response.data && response.data.successMessage) {
                Utils.createToast(response.data.successMessage);
            } else if (response.data && response.data.message) {
                Utils.createToast(response.data.message);
            }
            if (responseHandlers[id]) {
                if (!success) {
                    responseHandlers[id].reject(success);
                } else {
                    if (data.detail === 'Invalid token') {
                        if (Variable.getRefreshToken()) {
                            await refreshAccessToken();
                            Variable.setToken(localStorage.getItem("jwt"));
                        } else {
                            Utils.redirectToAuth();
                            Utils.createToast('Unauthorized: Redirecting to auth...');
                        }
                    }
                    responseHandlers[id].resolve(data);
                }
                delete responseHandlers[id];
            } else if (action) {
                if (successMessage && successMessage.length > 0) {
                    Utils.createToast(successMessage);
                } else if (message && message.length > 0) {
                    Utils.createToast(message);
                }
                switch (action) {
                    case 'update_quests':
                        // сделаем заброс на проверку списка принятых квестов
                        Variable.setUserQuests(await websocketRequest('/quest', {'action': 'get_user_quest'}));
                        break;
                    case 'update_chat':
                        await Chat.chat(false, data.messages);
                        break;
                    case 'update_mail':
                        Variable.setUserMails(await websocketRequest('/mail', {'action': 'get_messages'}));
                        Mail.updateCountMail(Variable.getUserMails());
                        break;
                }
            } else {
                console.warn(`No handler found for response ID: ${id}`);
            }
        } catch (e) {
            console.error("Failed to parse message:", e);
        }
    };

    websocket.onclose = async (event) => {
        websocketReady = false;
        if (Variable.getRefreshToken()) {
            await refreshAccessToken();
            Variable.setToken(localStorage.getItem("jwt"));
        } else {
            Utils.redirectToAuth();
            Utils.createToast('Unauthorized: Redirecting to auth...');
        }
        console.log("WebSocket connection closed. Reconnecting...");
        Utils.createToast('Соединение потеряно. Подключаемся...');
        setTimeout(() => initializeWebSocket(Variable.getToken()), 2000);
    };

    websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

// Функция, которая будет выполняться только после установки соединения
export function onWebSocketReady(callback) {
    if (websocketReady) {
        callback();  // Если WebSocket уже готов, выполняем сразу
    } else {
        // Если WebSocket не готов, отложим выполнение до установления соединения
        websocket.addEventListener('open', callback);
    }
}

async function requestWebSocket(endpoint, body = null) {
    // Формируем сообщение
    const id = Math.random().toString(36).substr(2, 9); // Генерируем уникальный ID запроса
    const message = {id, endpoint, body};
    if (!websocketReady) {
        console.error("WebSocket is not ready");
        messageQueue.push(JSON.stringify(message));
        return null;
    }

    // Возвращаем промис для асинхронного ожидания ответа
    return new Promise((resolve, reject) => {
        responseHandlers[id] = {resolve, reject};
        websocket.send(JSON.stringify(message));
    });
}

export async function websocketRequest(endpoint, body = null) {
    try {
        const responseData = await requestWebSocket(endpoint, body);
        if (responseData && responseData.success) {
            if (responseData.successMessage && responseData.successMessage.length) {
                //Utils.createToast(responseData.successMessage);
            }
            return responseData.data;
        } else if (responseData && responseData.message && responseData.message.length) {
            //Utils.createToast(responseData.message);
            return null;
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

initializeWebSocket(Variable.getToken());
