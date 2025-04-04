import json

from app.config.config import logger
from app.repositories.FeedbackRepository import FeedbackRepository
from app.utils.Json import format_error_response


async def feedback_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'save': save
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def save(body, db, current_user):
    if await FeedbackRepository(db).create_feedback(current_user['id'], body['title'], body['description']):
        return {
            "success": True,
            "data": {'saved': True},
            "message": None,
            "successMessage": 'Сообщение отправлено'
        }
    else:
        return {
            "success": False,
            "data": {'saved': False},
            "message": 'Ошибка',
            "successMessage": None
        }