import json

from app.config.config import logger
from app.repositories.PushSubscriptionRepository import PushSubscriptionRepository
from app.utils.Json import format_error_response


async def webpush_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'subscribe': subscribe,
        'unsubscribe': unsubscribe
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def subscribe(body, db, current_user):
    subscription = json.loads(body['subscription'])
    logger.debug(f"subscription: {subscription['keys']}")
    if await PushSubscriptionRepository(db).create_subscription(subscription['endpoint'], subscription['keys']['p256dh'], subscription['keys']['auth'], current_user['id']):
        return {
            "success": True,
            "data": None,
            "message": None,
            "successMessage": None
        }
    return {
        "success": False,
        "data": None,
        "message": 'Не удалось подписаться на уведомления',
        "successMessage": None
    }

async def unsubscribe(body, db, current_user):
    subscription_endpoint = body['subscription_endpoint']
    if await PushSubscriptionRepository(db).delete_subscription(subscription_endpoint, current_user['id']):
        return {
            "success": True,
            "data": None,
            "message": None,
            "successMessage": None
        }
    return {
        "success": False,
        "data": None,
        "message": 'Не удалось подписаться на уведомления',
        "successMessage": None
    }