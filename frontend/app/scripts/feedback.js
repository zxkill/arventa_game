import '../css/feedback.css'
import {websocketRequest} from "./websocket";
import Utils from "./utils";
import Variable from "./variable";
import Modal from "./modal";


function drawFeedbackWindow() {
    return `
        <form id="feedback-form">
          <label for="title">Тема:</label>
          <input type="text" name="title">
          <label for="description">Описание:</label>
          <textarea name="description" placeholder="Опишите вашу проблему или предложение..."></textarea>
          <div class="buttons">
            <button type="submit" id="save-btn">Отправить</button>
          </div>
        </form>
    `;
}

function events() {
    document.querySelector('#feedback-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        const title = document.querySelector('input[name="title"]').value;
        const description = document.querySelector('textarea[name="description"]').value;
        if (!title || !description || !description.trim().length) {
            Utils.createToast('Все поля обязательны для заполнения');
            return;
        }
        await websocketRequest('/feedback', {
            'action': 'save',
            'title': title,
            'description': description,
        }).then((response) => {
            if (response && response.saved === true) {
                Modal.closeModalHandler(e);
            }
        });
        return false;
    });
    return true;
}

const Feedback = {
    drawFeedbackWindow,
    events
}

export default Feedback;