import math
from app.config.config import logger
from app.services.users import get_interaction_radius, get_player_coords


# Утилита для расчета расстояния между двумя координатами
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Радиус Земли в метрах
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# проверим, находятся ли объекты на разрешенном для взаимодействия расстоянии
def check_range(lon1, lat1, current_user):
    player_coords = get_player_coords(current_user)
    if not player_coords:
        return False
    user_lon, user_lat = player_coords
    logger.debug(f"Координаты для расчета расстояния {lon1}, {lat1} {user_lon}, {user_lat}")
    logger.debug(
        f"Расстояние между объектами: {int(calculate_distance(lat1, lon1, user_lat, user_lon))}")
    if int(calculate_distance(lat1, lon1, user_lat, user_lon)) > get_interaction_radius(current_user):
        return False
    return True
