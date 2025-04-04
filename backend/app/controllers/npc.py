import json
from fastapi.responses import JSONResponse
from app.repositories.PointRepository import PointRepository
from app.config.config import logger
from app.services.maps import check_range
from app.utils.Json import format_error_response


async def npc_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get_npc': get_npc
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def get_npc(body, db, current_user):
    npc_id = body['npc_id']
    if not npc_id:
        return JSONResponse(status_code=400, content=[])

    npc_id = int(npc_id[1:])

    # Достаем данные о точке
    pointRep = PointRepository(db)
    point = await pointRep.get_point_by_id(npc_id)

    if not check_range(point['lon'], point['lat'], current_user):
        return {
            "success": False,
            "data": None,
            "message": "Подойдите ближе для взаимодействия"
        }

    if point['type'] != 'npc':
        return {
            "success": False,
            "data": None,
            "message": "Ошибка. NPC не найден"
        }

    point_data = json.loads(point['data'])

    # Проверим, какие квесты уже выполнены или начаты
    # query = """
    #     SELECT
    #         quest_id
    #     FROM user_quests
    #     WHERE
    #         user_id = $1 AND quest_id = ANY($2)
    # """
    # rowsUserQuest = await db.fetch(query, current_user['id'], point_data['quests'])

    # Преобразуем результаты в список выполненных/начатых квестов
    # accepted_quests = [row['quest_id'] for row in rowsUserQuest]
    # logger.debug(f"Квесты которые уже выполнены или начаты: {accepted_quests}")

    # Получим данные для новых квестов
    # quest = await QuestRepository(db).get_new_quest(point_data['quests'], accepted_quests)
    # logger.debug(f"Доступный квест: {quest}")

    return {
        "success": True,
        "data": None,
        "successMessage": "Квест успешно найден"
    }
