from app.config.config import logger
from app.repositories.AvatarRepository import AvatarRepository
from app.services.webpush import send_notification
from app.utils.Json import format_error_response


async def avatar_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get': get
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def get(body, db, current_user):
    avatars = []
    avatars_record = await AvatarRepository(db).get_avatar_for_user(current_user['id'])
    if avatars is not None:
        for avatar in avatars_record:
            avatars.append({
                'id': avatar['id'],
                'title': avatar['title'],
                'description': avatar['description'],
                'url': avatar['url'],
            })

    return {
        "success": True,
        "data": avatars,
        "message": None,
        "successMessage": None
    }
