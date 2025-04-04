import json

from app.config.config import logger, asyncRedis
from app.repositories.UserProfileRepository import UserProfileRepository

from app.utils.Json import format_error_response


async def settings_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'save': save
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def save(body, db, current_user):
    settings = json.loads(body['settings'])
    logger.debug(f"settings: {settings}")
    if await UserProfileRepository(db).save_settings(current_user['id'], settings):
        return {
            "success": True,
            "data": {'saved': True},
            "message": None,
            "successMessage": 'Настройки сохранены'
        }
    else:
        return {
            "success": False,
            "data": {'saved': False},
            "message": 'Ошибка сохранения',
            "successMessage": None
        }