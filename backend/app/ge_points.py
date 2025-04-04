import time
import random
import numpy as np
import psycopg2
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely import vectorized
from pyproj import CRS, Transformer

# Подключение к базе данных
conn = psycopg2.connect("postgresql://user:password@db:5432/game_db")
cursor = conn.cursor()

# Конфигурация города
#CITY_NAME = "Agapovka, Russia"
#CITY_NAME = "Lipetsk, Russia"
#CITY_NAME = "Chelyabinsk, Russia"
CITY_NAME = "Magnitogorsk, Russia"
DENSITY_M2 = 6000  # 1 точка на 225 м² (примерно 15x15 метров)


def load_city_data(city_name):
    """
    Загружает границы города и водные объекты.
    """
    start = time.time()
    # Границы города
    gdf_city = ox.geocode_to_gdf(city_name)
    city_polygon = gdf_city.geometry.iloc[0]

    # Водные объекты
    gdf_water = ox.features_from_place(
        city_name,
        tags={
            "natural": "water",
            "waterway": True,
            "landuse": "reservoir",
            "wetland": True,
            "leisure": "swimming_pool"
        }
    )

    # Фильтрация водных полигонов
    water_polygons = [geom for geom in gdf_water.geometry if isinstance(geom, (Polygon, MultiPolygon))]
    combined_water = gpd.GeoSeries(water_polygons).union_all() if water_polygons else None
    elapsed = time.time() - start
    print(f"[load_city_data] Выполнено за {elapsed:.2f} секунд")
    return city_polygon, combined_water


def calculate_area_m2(polygon):
    """
    Рассчитывает площадь полигона в квадратных метрах, используя UTM-проекцию.
    """
    start = time.time()
    centroid = polygon.centroid
    utm_zone = int((np.floor((centroid.x + 180) / 6) % 60) + 1)
    utm_crs = CRS.from_dict({
        'proj': 'utm',
        'zone': utm_zone,
        'south': centroid.y < 0
    })
    transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
    utm_polygon = Polygon([transformer.transform(x, y) for x, y in polygon.exterior.coords])
    area = utm_polygon.area
    elapsed = time.time() - start
    print(f"[calculate_area_m2] Выполнено за {elapsed:.4f} секунд")
    return area


def load_regions():
    """
    Загружает регионы из БД.
    Таблица regions имеет поля: id, top_left, bottom_right (типа geography).
    Приводим колонки к geometry и формируем прямоугольный полигон региона.
    """
    start = time.time()
    cursor.execute("""
        SELECT id, 
               ST_X(top_left::geometry) AS top_left_x, ST_Y(top_left::geometry) AS top_left_y,
               ST_X(bottom_right::geometry) AS bottom_right_x, ST_Y(bottom_right::geometry) AS bottom_right_y
        FROM regions
    """)
    rows = cursor.fetchall()
    region_list = []
    for reg_id, tl_x, tl_y, br_x, br_y in rows:
        poly = Polygon([
            (tl_x, tl_y),
            (br_x, tl_y),
            (br_x, br_y),
            (tl_x, br_y),
            (tl_x, tl_y)
        ])
        region_list.append((reg_id, poly))
    elapsed = time.time() - start
    print(f"[load_regions] Выполнено за {elapsed:.2f} секунд")
    return region_list


def generate_random_points_vectorized_batches(city_polygon, combined_water, density_m2, region_list, batch_size=100000):
    """
    Генерирует точки пакетно (батчами) с использованием векторизации.

    Алгоритм:
      1. Вычисляется целевое количество точек на основе площади города.
      2. Пока общее число вставленных точек меньше целевого, генерируется батч кандидатов.
      3. Для каждого батча с помощью векторизованных операций отбираются точки,
         попадающие в город и не попадающие в водную область.
      4. Выполняется пространственный join кандидатов с регионами.
      5. Для полученных точек формируется пакет данных и сразу вставляется в БД.
    """
    start_total = time.time()
    area = calculate_area_m2(city_polygon)
    target_count = int(area / density_m2)
    print(f"[generate_random_points_vectorized_batches] Целевое количество точек: {target_count}")

    minx, miny, maxx, maxy = city_polygon.bounds
    total_inserted = 0

    # Подготовка для типов точек
    resource_ids = list(range(1, 7))
    monster_ids = list(range(1, 11))
    portal_ids = list(range(1, 9))

    # Преобразуем список регионов в GeoDataFrame
    regions_df = pd.DataFrame([{'region_id': reg_id, 'geometry': poly} for reg_id, poly in region_list])
    gdf_regions = gpd.GeoDataFrame(regions_df, crs="EPSG:4326")

    batch_num = 0
    while total_inserted < target_count:
        batch_num += 1
        start_batch = time.time()
        # Генерируем батч случайных точек
        xs = np.random.uniform(minx, maxx, batch_size)
        ys = np.random.uniform(miny, maxy, batch_size)

        # Векторизированная проверка попадания в город
        in_city = vectorized.contains(city_polygon, xs, ys)

        # Проверка водных объектов (если они есть) через vectorized.contains
        if combined_water is not None:
            in_water = vectorized.contains(combined_water, xs, ys)
            not_in_water = ~in_water
        else:
            not_in_water = np.full(batch_size, True)

        mask = in_city & not_in_water
        xs_filtered = xs[mask]
        ys_filtered = ys[mask]

        # Если нет кандидатов в этом батче, переходим к следующему
        if len(xs_filtered) == 0:
            continue

        # Преобразуем кандидатов в GeoDataFrame
        df_candidates = pd.DataFrame({'lon': xs_filtered, 'lat': ys_filtered})
        gdf_candidates = gpd.GeoDataFrame(
            df_candidates,
            geometry=gpd.points_from_xy(df_candidates.lon, df_candidates.lat),
            crs="EPSG:4326"
        )

        # Пространственный join: оставляем только точки, попадающие в регион
        gdf_joined = gpd.sjoin(gdf_candidates, gdf_regions, how="inner", predicate="within")
        candidate_points = gdf_joined[['lon', 'lat', 'region_id']].to_records(index=False)

        # Если в этом батче получилось больше точек, чем нужно для достижения цели, выбираем случайно
        remaining = target_count - total_inserted
        if len(candidate_points) > remaining:
            # Используем pandas DataFrame для выборки
            df_candidates_joined = pd.DataFrame(candidate_points, columns=["lon", "lat", "region_id"])
            df_candidates_joined = df_candidates_joined.sample(n=remaining, random_state=42)
            candidate_points = df_candidates_joined.to_records(index=False)

        # Формируем данные для вставки
        batch_data = []
        for lon, lat, region_id in candidate_points:
            random_num = random.random()
            if random_num < 0.65:
                point_type = 'resources'
                object_id = random.choice(resource_ids)
            elif random_num < 0.98:  # 65% + 33% = 98%
                point_type = 'monsters'
                object_id = random.choice(monster_ids)
            else:  # Оставшиеся 2%
                point_type = 'portals'
                object_id = random.choice(portal_ids)
            batch_data.append((float(lat), float(lon), point_type, int(object_id), int(region_id)))

        # Вставляем данные в БД
        if batch_data:
            cursor.executemany(
                """
                INSERT INTO points (coordinates, type, object_id, region_id)
                VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s, %s)
                """,
                batch_data
            )
            conn.commit()
            inserted = len(batch_data)
            total_inserted += inserted
        elapsed_batch = time.time() - start_batch
        print(
            f"[Batch {batch_num}] Обработано {len(candidate_points)} кандидатов, вставлено: {inserted} точек, всего вставлено: {total_inserted}/{target_count}, время батча: {elapsed_batch:.2f} секунд")
    elapsed_total = time.time() - start_total
    print(f"[generate_random_points_vectorized_batches] Общая генерация точек заняла {elapsed_total:.2f} секунд")
    return total_inserted


# Основной процесс
t0 = time.time()
city_polygon, combined_water = load_city_data(CITY_NAME)
t1 = time.time()
region_list = load_regions()
t2 = time.time()
generated_count = generate_random_points_vectorized_batches(city_polygon, combined_water, DENSITY_M2, region_list,
                                                            batch_size=100000)
t3 = time.time()

print(f"\n[Main] load_city_data: {t1 - t0:.2f} секунд")
print(f"[Main] load_regions: {t2 - t1:.2f} секунд")
print(f"[Main] generate_random_points_vectorized_batches: {t3 - t2:.2f} секунд")

# Фиксация изменений и закрытие соединения
conn.commit()
cursor.close()
conn.close()
print(f"Успешно создано {generated_count} точек!")
