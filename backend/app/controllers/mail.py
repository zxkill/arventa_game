from app.repositories.MailRepository import MailRepository
from app.repositories.UserRepository import UserRepository
from app.services.text import text_to_html
from app.services.webpush import send_notification
from app.utils.Json import format_error_response
from app.websocket import manager
from app.config.config import logger


async def mail_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get_messages': get_messages,
        'send': send,
        'read': read,
        'delete': delete
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def get_messages(body, db, current_user):
    messages = await MailRepository(db).get_messages_by_user_id(current_user['id'])
    mails = []
    for message in messages:
        user = await UserRepository(db).get_user_by_id(message['sender_id'])
        mails.append({
            'id': message['id'],
            'sender_name': user['username'],
            'subject': message['subject'],
            'message': text_to_html(message['message']),
            'datetime': message['created_at'].strftime('%Y-%m-%d %H:%M:%SZ'),
            'is_read': message['is_read']
        })
    return {
        "success": True,
        "data": mails,
        "message": None,
        "successMessage": None
    }


async def send(body, db, current_user):
    if body['recipient_id'] == current_user['id']:
        return format_error_response('Нельзя отправить письмо самому себе')

    recipient = UserRepository(db).get_user_by_id(int(body['recipient_id']))
    if not recipient:
        return format_error_response('Получатель не найден')

    if await MailRepository(db).add_message(current_user['id'], int(body['recipient_id']), body['subject'],
                                            body['message']):
        # отправим получателю сигнал о новом письме
        if not await manager.send_personal_message({'action': 'update_mail'}, int(body['recipient_id'])):
            try:
                await send_notification(
                    'Новое письмо',
                    'Вам пришло письмо от ' + current_user['username'] + '. Войдите в игру, чтобы прочитать его.',
                    db,
                    int(body['recipient_id'])
                )
            except Exception as e:
                logger.exception(e)

        return {
            "success": True,
            "data": None,
            "message": None,
            "successMessage": "Письмо отправлено успешно"
        }
    else:
        return {
            "success": False,
            "data": None,
            "message": 'Ошибка отправки',
            "successMessage": None
        }


async def read(body, db, current_user):
    mail_id = int(body['mail_id'])
    if not mail_id:
        return format_error_response('Некорректный запрос')

    if not await MailRepository(db).check_allow_message(mail_id, current_user['id']):
        return format_error_response('Некорректный запрос')

    if await MailRepository(db).read(mail_id):
        return {
            "success": True,
            "data": {'read': True},
            "message": None,
            "successMessage": None
        }
    else:
        return format_error_response('Не удалось поставить отметку о прочтении')

async def delete(body, db, current_user):
    mail_id = int(body['mail_id'])
    if not mail_id:
        return format_error_response('Некорректный запрос')

    if not await MailRepository(db).check_allow_message(mail_id, current_user['id']):
        return format_error_response('Некорректный запрос')

    if await MailRepository(db).delete(mail_id):
        return {
            "success": True,
            "data": {'deleted': True},
            "message": None,
            "successMessage": None
        }
    else:
        return format_error_response('Не удалось поставить отметку о прочтении')
