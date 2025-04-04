import json

from app.repositories.PointRepository import PointRepository
from app.repositories.QuestRepository import QuestRepository
from app.repositories.UserItemRepository import UserItemRepository
from app.repositories.UserQuestRepository import UserQuestRepository
from app.repositories.UserRepository import UserRepository
from app.services.maps import check_range
from app.services.quest import enrich_quest_data
from app.services.text import text_to_html
from app.services.users import replace_user_data
from app.config.config import logger
from app.utils.Json import format_error_response
from app.utils.User import is_overload


async def quest_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'accept_quest': accept_quest,
        'delete_user_quest': delete_user_quest,
        'get_user_quest': get_user_quest,
        'complete_quest': complete_quest,
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def accept_quest(body, db, current_user):
    quest_id = int(body['quest_id'])
    object_id = body['object_id']
    if not quest_id:
        return {
            "success": False,
            "data": None,
            "message": "Ошибка. Попробуйте еще раз."
        }

    npc_id = int(object_id[1:])
    if not npc_id:
        return {
            "success": False,
            "data": None,
            "message": "Ошибка. Попробуйте еще раз."
        }

    # получим данные о точке
    pointRep = PointRepository(db)
    point = await pointRep.get_point_by_id(npc_id)
    logger.debug(f"Точка: {point}")
    if not point:
        return {
            "success": False,
            "data": None,
            "message": "Ошибка. Попробуйте еще раз."
        }

    point_data = json.loads(point['data'])
    # сначала перепроверим, а можем ли мы принять квест
    logger.debug(f"Доступные квесты у точки: : {point_data['quests']}")

    # проверим, есть ли у этой точки запрашиваемый квест
    if quest_id not in point_data['quests']:
        return {
            "success": False,
            "data": None,
            "message": "У данного персонажа нет этого квеста."
        }

    # проверяем расстояние
    if not check_range(point['lon'], point['lat'], current_user):
        return {
            "success": False,
            "data": None,
            "message": "Подойдите ближе."
        }
    user_quest_rep = UserQuestRepository(db)

    # вдруг квест уже принят или даже выполнен
    if await user_quest_rep.is_quest_already_use(current_user['id'],
                                                 quest_id):
        return {
            "success": False,
            "data": None,
            "message": "У вас уже есть этот квест."
        }

    # если все проверки успешны, то принимаем квест
    try:
        await user_quest_rep.add_user_quest(current_user['id'], quest_id)
        return {
            "success": True,
            "data": None,
            "successMessage": "Квест принят.",
            "message": None
        }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "message": f"Ошибка. Попробуйте еще раз. {e}"
        }
    except RuntimeError as e:
        return {
            "success": False,
            "data": None,
            "message": f"Ошибка. Попробуйте еще раз. {e}"
        }


async def delete_user_quest(body, db, current_user):
    quest_id = body['quest_id']
    if not quest_id:
        return {
            "success": False,
            "data": None,
            "message": "Вы не выбрали квест для отмены."
        }

    # проверим, есть ли у пользователя этот квест и что он еще не сдан
    user_quest = await UserQuestRepository(db).get_user_quest_by_id(current_user['id'], quest_id)
    if not user_quest or user_quest['status'] != 'in_progress':
        return {
            "success": False,
            "data": None,
            "message": "Вы не можете отменить этот квест."
        }

    if not await UserQuestRepository(db).delete_user_quest(current_user['id'], quest_id):
        return {
            "success": False,
            "data": None,
            "message": "Не удалось отменить квест. Попробуйте снова."
        }

    return {
        "success": True,
        "data": None,
        "message": None,
        "successMessage": "Квест успешно отменен."
    }


async def get_user_quest(body, db, current_user):
    # получим все повторяемые квесты
    repeatable_quests = await QuestRepository(db).get_repeatable_quests(current_user['id'])
    logger.debug(f"repeatable_quests: {repeatable_quests}")

    if repeatable_quests:
        for quest_id in repeatable_quests:
            await UserQuestRepository(db).add_user_quest(current_user['id'], quest_id['id'])

    list_quest_id = await UserQuestRepository(db).get_quest_in_progress_by_user_id(current_user['id'])
    logger.debug(f"list_quest_id: {list_quest_id}")
    if not list_quest_id:
        return {
            "success": True,
            "data": [],
            "message": 'Вы пока не взяли ни одного квеста'
        }

    # Получаем квесты
    quests = await QuestRepository(db).get_quest_by_ids(list_quest_id)

    # Формируем список квестов с дополненной информацией
    quest_list = []
    for quest in quests:
        # обогащаем данные о квесте, подтянем детальную инфу о предметах и прочем
        quest, reward, detailed_conditions = await enrich_quest_data(quest, db, current_user, True)
        description = text_to_html(replace_user_data(quest['description'], current_user))
        if quest['completed'] and 'completed_description' in quest and quest['completed_description']:
            description = text_to_html(replace_user_data(quest['completed_description'], current_user))
        # Добавляем обработанный квест в список
        quest_list.append({
            'id': quest['id'],
            'name': quest['name'],
            'completed': quest['completed'],
            'description': description,
            'reward': reward,
            'conditions': detailed_conditions,
        })
    logger.debug(f"quest_list {quest_list}")
    return {
        "success": True,
        "data": quest_list,
        "message": None,
        "successMessage": None
    }


async def complete_quest(body, db, current_user):
    quest_id = int(body['quest_id'])

    if await is_overload(db, current_user):
        return {
            "success": False,
            "data": None,
            "message": "У вас перегруз. Избавьтесь от лишних предметов",
            "successMessage": None
        }

    async with db.transaction():  # Начало транзакции
        # Проверка статуса квеста
        quest_status = await UserQuestRepository(db).get_user_quest_by_id(current_user['id'], quest_id)
        logger.debug(f"Quest status {quest_status}")
        if not quest_status or quest_status["status"] != "completed":
            return {
                "success": False,
                "data": None,
                "message": "Квест не выполнен или не взят.",
                "successMessage": None
            }

        # Получение информации о квесте
        quest = await QuestRepository(db).get_quest_by_id(quest_id)
        if not quest:
            return {
                "success": False,
                "data": None,
                "message": "Квест не найден.",
                "successMessage": None
            }

        reward = json.loads(quest["reward"])
        # Начисление денег
        silver_reward = int(reward.get('money', {}).get('silver', 0))
        logger.debug(f"Quest reward silver {silver_reward}")
        if silver_reward > 0:
            if not await UserRepository(db).update_silver(current_user['id'], silver_reward):
                return {
                    "success": False,
                    "data": None,
                    "message": "Не удалось начислить серебро.",
                    "successMessage": None
                }

        # Начисление предметов
        user_item_rep = UserItemRepository(db)
        for item in reward.get("items", []):
            if not await user_item_rep.add_item(current_user['id'], item["id"], item["quantity"]):
                return {
                    "success": False,
                    "data": None,
                    "message": "Ошибка добавления предмета.",
                    "successMessage": None
                }

        # Обновление статуса квеста
        if not await UserQuestRepository(db).update_status_user_quest(current_user['id'], quest_id):
            return {
                "success": False,
                "data": None,
                "message": "Ошибка обновления статуса квеста.",
                "successMessage": None
            }

        """
        После успешной сдачи одного квеста, необходимо автоматически назначить следующий, Но если это основная линия
        """
        result = ''
        if not quest['is_repeatable']:
            # найдем следующий квест за quest
            new_quest = await QuestRepository(db).get_next_by_order(quest)
            logger.debug(f"New Quest {new_quest}")
            if new_quest:
                if await UserQuestRepository(db).add_user_quest(current_user['id'], new_quest['id']):
                    result = ' Вам назначен новый квест'

        # Возврат успешного ответа
        return {
            "success": True,
            "data": None,
            "successMessage": f"Квест '{quest['name']}' завершен, награда начислена!{result}",
            "message": None
        }
