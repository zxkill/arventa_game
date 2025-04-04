import json
import html

from app.config.config import logger
from app.repositories.UserProfileRepository import UserProfileRepository
from app.utils.Json import format_error_response


async def profile_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'save': save
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def save(body, db, current_user):
    profile = {
        'name': html.escape(body['name']),
        'bio': html.escape(body['bio']),
        'birthday': html.escape(body['birthday']) if 'birthday' in body else None,
        'avatar_id': int(body['avatar_id']),
    }
    # todo надо будет проверять, можно ли пользователю выбрать данный аватар
    if await UserProfileRepository(db).save_profile(current_user['id'], profile):
        return {
            "success": True,
            "data": {'saved': True},
            "message": None,
            "successMessage": 'Данные профиля успешно сохранены'
        }
    else:
        return {
            "success": False,
            "data": {'saved': False},
            "message": 'Ошибка',
            "successMessage": None
        }