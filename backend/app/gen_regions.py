import psycopg2

# Подключение к базе данных
conn = psycopg2.connect('postgresql://user:password@db:5432/game_db')
cursor = conn.cursor()

# Размер ячейки в градусах
LAT_STEP = 5
LON_STEP = 5

# Генерация ячеек
region_id = 1
for lat in range(-90, 90, LAT_STEP):
    for lon in range(-180, 180, LON_STEP):
        # Верхняя левая точка
        top_left = (lon, lat)
        # Нижняя правая точка
        bottom_right = (lon + LON_STEP, lat + LAT_STEP)

        # Имя региона
        region_name = f"Region {region_id}"

        # Вставка в базу данных
        cursor.execute(
            """
            INSERT INTO regions (name, top_left, bottom_right)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """,
            (region_name, top_left[0], top_left[1], bottom_right[0], bottom_right[1])
        )
        region_id += 1

# Подтверждение изменений и закрытие подключения
conn.commit()
cursor.close()
conn.close()

print("Ячейки успешно сгенерированы!")
