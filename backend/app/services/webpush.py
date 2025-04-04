import json

from pywebpush import webpush, WebPushException
from app.config.config import logger
from app.config.config import VAPID_PRIVATE_KEY, VAPID_CLAIMS
from app.repositories.PushSubscriptionRepository import PushSubscriptionRepository

# try:
#     await send_notification('Арвента ждет тебя!', 'Будь как дома путник', db, current_user)
# except Exception as e:
#     logger.error(e)


async def send_notification(title, body, db, user_id:int=None):
    if user_id:
        # отправляем на все подписки пользователя
        subscriptions = await PushSubscriptionRepository(db).get_subscriptions_by_user(user_id)
    else:
        # отправляем всем
        subscriptions = await PushSubscriptionRepository(db).get_all_subscriptions()
    logger.debug(f"subscriptions: {subscriptions}")
    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub['endpoint'],
            "keys": {
                "p256dh": sub['p256dh'],
                "auth": sub['auth'],
            }
        }
        message = {
            "title": title,
            "body": body,
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(message),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code == 410:
                # Здесь реализуйте логику удаления подписки из вашей БД по subscription_info['endpoint']
                await PushSubscriptionRepository(db).delete_subscription(subscription_info['endpoint'], sub['user_id'])
            else:
                print("Ошибка при отправке push-уведомления:", repr(ex))

    return True