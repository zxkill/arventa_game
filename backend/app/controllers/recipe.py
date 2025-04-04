import json
import time

from app.repositories.ItemRepository import ItemRepository
from app.config.config import logger, asyncRedis
from app.repositories.PlayerItemProgressRepository import PlayerItemProgressRepository
from app.repositories.RecipeRepository import RecipeRepository
from app.repositories.UserItemRepository import UserItemRepository
from app.services.ActionsEvent import ActionsEvent
from app.services.QuestEvent import handle_event, QuestEvent
from app.services.item import ItemHelper
from app.utils.Json import format_error_response
from app.utils.User import is_overload


async def recipe_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get_recipes': get_recipes,
        'make_recipe': make_recipe,
        'get_make_result': get_make_result
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def get_recipes(body, db, current_user):
    recipe_data = []
    recipes = await RecipeRepository(db).get_recipes()
    if recipes:
        item_ids, resource_ids = set(), set()
        for recipe in recipes:
            item_ids.add(recipe['item_id'])
            resources = json.loads(recipe['materials_required']).get('resources', [])
            for resource in resources:
                resource_ids.add(resource['resource_id'])
        items_data = await ItemRepository(db).get_items_by_id(list(item_ids | resource_ids))
        item_data_map = {item['id']: item for item in items_data}
        for recipe in recipes:
            item_data = item_data_map.get(recipe['item_id'], {})
            item_data['item_id'] = item_data['id']
            # поставим сколько предметов будет получено при крафте
            item_data['quantity'] = recipe['quantity_crafting_item']
            if 'effect' in item_data and item_data['effect']:
                logger.debug(f"recipe 781 {item_data['effect']}")
                if item_data['effect'] == 'null':
                    item_data['effect'] = {}
                else:
                    item_helper = ItemHelper(db, current_user)
                    item_data['effect'] = item_helper.item_effects_mapped(item_data['effect'])
                    logger.debug(f"recipe 782 {item_data['effect']}")
            logger.debug(f"recipe 5")
            recipe_data.append({
                "id": recipe['id'],
                "item": item_data,
                "materials_required": [
                    {
                        "resource": item_data_map.get(resource['resource_id'], {}),
                        "count": resource['count']
                    }
                    for resource in json.loads(recipe['materials_required']).get('resources', [])
                ]
            })

        logger.debug(f"recipe_data: {recipe_data}")
        # Сортировка по resource и tier предмета
        recipe_data = sorted(
            recipe_data,
            key=lambda x: (
                str(x["item"].get("resource_type", "")).lower().strip(),  # Убираем регистр и пробелы
                int(x["item"].get("tier", 0))  # Сортируем как числа
            )
        )

    return {
        "success": True,
        "data": recipe_data,
        "message": None,
        "successMessage": None
    }


async def check_recipe_exists(recipe_id, db, current_user):
    if not recipe_id:
        return format_error_response('Такого рецепта не существует1')

    recipe = await RecipeRepository(db).get_recipe(recipe_id)
    if not recipe:
        return format_error_response('Такого рецепта не существует2')
    if isinstance(recipe, dict) and recipe.get('error'):
        return recipe

    materials = recipe.get('materials_required', {})
    resource_ids = []
    materials = json.loads(str(materials))
    for material in materials['resources']:
        resource_ids.append(material['resource_id'])
    user_item_data_map = await get_user_item_data_map(db, resource_ids, current_user['id'])
    if not await has_required_resources(materials, user_item_data_map):
        return format_error_response('У вас нет необходимых ресурсов для крафта')
    return recipe


async def get_user_item_data_map(db, resource_ids, user_id):
    if resource_ids:
        user_items = await UserItemRepository(db).get_user_item_by_item_ids(resource_ids, user_id)
        return {item['item_id']: item['quantity'] for item in user_items}
    return {}


async def has_required_resources(materials, user_item_data_map):
    return all(
        user_item_data_map.get(resource['resource_id'], 0) >= resource['count']
        for resource in materials['resources']
    )


async def make_recipe(body, db, current_user):
    recipe_id = int(body['recipe_id'])
    recipe = await check_recipe_exists(recipe_id, db, current_user)
    cache_key = f"make.recipe:user.id:{current_user['id']}"
    cache_key_user = f"make.recipe:{recipe_id}:user.id:{current_user['id']}"
    time_is_out = await asyncRedis.get(cache_key_user)
    if time_is_out:
        return format_error_response('Вы уже создаете этот предмет')
    already_make = await asyncRedis.get(cache_key)
    if already_make:
        return format_error_response('Вы уже создаете другой предмет')
    if await is_overload(db, current_user):
        return format_error_response('У вас перегруз. Избавьтесь от лишних предметов')
    if type(recipe) is dict:
        return recipe
    # поставим просто метку, что мы что-то начали крафтить, чтобы параллельно не начать другой крафт
    await asyncRedis.setex(cache_key, recipe['crafting_time'], 1)
    await asyncRedis.setex(cache_key_user, 180, time.time() + (recipe['crafting_time']))

    return {
        "success": True,
        "data": {
            'crafting_time': recipe['crafting_time'],
        },
        "message": None,
        "successMessage": None
    }


async def get_make_result(body, db, current_user):
    recipe_id = int(body['recipe_id'])
    cache_key_user = f"make.recipe:{recipe_id}:user.id:{current_user['id']}"
    time_is_out = await asyncRedis.get(cache_key_user)
    if not time_is_out:
        return format_error_response('Что-то пошло не так. Попробуйте снова')
    logger.debug(f"time_is_out: {time_is_out}")
    cur_time = time.time()
    logger.debug(f"cur_time: {cur_time}")
    if float(time_is_out) > cur_time:
        return format_error_response('Предмет еще создается')
    await asyncRedis.delete(cache_key_user)
    async with db.transaction():
        logger.debug(f"get_make_result: {body}")
        recipe = await check_recipe_exists(recipe_id, db, current_user)
        logger.debug(f"get_make_result2: {body}")
        if type(recipe) is dict:
            return recipe
        # Добавляем предмет игроку
        logger.debug(f"get_make_result3: {body}")
        await UserItemRepository(db).add_item(current_user['id'], recipe['item_id'], recipe['quantity_crafting_item'])
        logger.debug(f"get_make_result4: {body}")
        event = QuestEvent(action='craft', target_id=recipe['item_id'], quantity=1, user_id=current_user['id'])
        await handle_event(event, db)

        await ActionsEvent(action='craft', user_id=current_user['id']).handle_event()

        logger.debug(f"get_make_result5: {body}")
        # todo надо добавить еще событие на общее отслеживание действий
        # прокачаем навык крафта
        items = await ItemRepository(db).get_items_by_id([recipe['item_id']])
        item = items[0]
        experience = 3  # todo тут можно подумать над прогрессивной шкалой
        await PlayerItemProgressRepository(db).update_progress(current_user['id'], 'craft', experience, item['resource_type'])
        # соберем информацию о предметах которые нужно забрать
        resource_ids = []
        resource_map = {}
        materials = json.loads(recipe.get('materials_required', ''))
        for resource in materials['resources']:
            resource_ids.append(resource['resource_id'])
            resource_map[resource['resource_id']] = resource['count']

        logger.debug(f"resource_map: {resource_map}")
        user_items = await UserItemRepository(db).get_user_item_by_item_ids(resource_ids, current_user['id'])
        logger.debug(f"user_items: {user_items}")
        for user_item in user_items:
            logger.debug(f"user_item: {user_item}")
            logger.debug(f"resource_map : {resource_map[user_item['item_id']]}")
            await UserItemRepository(db).destroy(user_item['id'], user_item['quantity'],
                                                 resource_map[user_item['item_id']])
    return {
        "success": True,
        "data": None,
        "message": None,
        "successMessage": 'Предмет успешно создан'
    }
