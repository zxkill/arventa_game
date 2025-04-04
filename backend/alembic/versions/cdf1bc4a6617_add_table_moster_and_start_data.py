"""add table moster and start data

Revision ID: cdf1bc4a6617
Revises: 635d5ce21be4
Create Date: 2024-12-30 15:48:00.476144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cdf1bc4a6617'
down_revision: Union[str, None] = '635d5ce21be4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("TRUNCATE TABLE user_items RESTART IDENTITY CASCADE;")
    op.execute("TRUNCATE TABLE items RESTART IDENTITY CASCADE;")
    op.execute("""
        INSERT INTO items (name, type, rarity, damage, armor, effect, resource_type, weight, price, is_stackable, stack_size, description, geometry, is_equippetable, body_part, tier)
VALUES
-- Ресурсы
('Дубовая древесина', 'Ресурс', 'Обычный', 0, 0, '{}', 'Древесина', 2.5, 10, true, 50, 'Базовая древесина для крафта.', NULL, false, NULL, 1),
('Железная руда', 'Ресурс', 'Обычный', 0, 0, '{}', 'Руда', 3.0, 15, true, 30, 'Руда для переплавки в слитки.', NULL, false, NULL, 1),
('Волчья шкура', 'Ресурс', 'Необычный', 0, 0, '{}', 'Шкура', 1.5, 25, true, 20, 'Мягкая и прочная шкура волка.', NULL, false, NULL, 2),
('Медная руда', 'Ресурс', 'Обычный', 0, 0, '{}', 'Руда', 2.8, 12, true, 40, 'Медь для создания инструментов.', NULL, false, NULL, 1),
('Ткань', 'Ресурс', 'Обычный', 0, 0, '{}', 'Ткань', 0.5, 8, true, 100, 'Материал для шитья и крафта.', NULL, false, NULL, 1),
('Золотая руда', 'Ресурс', 'Редкий', 0, 0, '{}', 'Руда', 5.0, 50, true, 20, 'Редкий материал для создания украшений.', NULL, false, NULL, 4),
('Серебряная руда', 'Ресурс', 'Необычный', 0, 0, '{}', 'Руда', 4.0, 35, true, 25, 'Используется в ювелирном деле.', NULL, false, NULL, 3),
('Мифриловая руда', 'Ресурс', 'Легендарный', 0, 0, '{}', 'Руда', 6.0, 100, true, 10, 'Сверхпрочный материал для создания редкого оружия.', NULL, false, NULL, 7),
('Шелковая нить', 'Ресурс', 'Необычный', 0, 0, '{}', 'Ткань', 0.2, 15, true, 200, 'Тонкая нить для создания деликатной одежды.', NULL, false, NULL, 2),
('Магическая эссенция', 'Ресурс', 'Эпический', 0, 0, '{}', 'Эссенция', 0.1, 250, true, 10, 'Редкий ресурс для создания магических предметов.', NULL, false, NULL, 6),
-- Оружие
('Железный меч', 'Оружие', 'Обычный', 25, 0, '{"strength": 2}', NULL, 3.5, 50, false, 0, 'Базовый меч из железа.', NULL, true, 'right_hand', 2),
('Стальной двуручный меч', 'Оружие', 'Редкий', 40, 0, '{"strength": 4}', NULL, 4.0, 100, false, 0, 'Хорошо выкованный двуручный меч.', NULL, true, 'right_hand', 4),
('Кинжал', 'Оружие', 'Обычный', 15, 0, '{"dexterity": 3}', NULL, 1.5, 35, false, 0, 'Быстрое и лёгкое оружие.', NULL, true, 'right_hand', 1),
('Боевой топор', 'Оружие', 'Редкий', 50, 0, '{"strength": 5}', NULL, 6.0, 150, false, 0, 'Мощное оружие для ближнего боя.', NULL, true, 'right_hand', 5),
('Лук охотника', 'Оружие', 'Необычный', 35, 0, '{"dexterity": 4}', NULL, 2.5, 80, false, 0, 'Лёгкий и точный лук.', NULL, true, 'right_hand', 3),
('Магический посох', 'Оружие', 'Эпический', 60, 0, '{"intelligence": 7}', NULL, 3.0, 300, false, 0, 'Посох с магической силой.', NULL, true, 'right_hand', 6),
('Арбалет', 'Оружие', 'Необычный', 45, 0, '{"dexterity": 5}', NULL, 4.5, 120, false, 0, 'Мощное дальнобойное оружие.', NULL, true, 'right_hand', 4),
('Молот титанов', 'Оружие', 'Легендарный', 70, 0, '{"strength": 10}', NULL, 8.0, 500, false, 0, 'Огромный молот, сокрушающий врагов.', NULL, true, 'right_hand', 7),
('Клинок теней', 'Оружие', 'Эпический', 55, 0, '{"dexterity": 6}', NULL, 2.0, 350, false, 0, 'Лёгкий и острый клинок.', NULL, true, 'right_hand', 5),
('Эльфийский лук', 'Оружие', 'Легендарный', 65, 0, '{"dexterity": 8}', NULL, 2.8, 400, false, 0, 'Идеальный лук для дальнего боя.', NULL, true, 'right_hand', 6),
-- Броня
('Кожаная броня', 'Броня', 'Обычный', 0, 15, '{"dexterity": 2}', NULL, 6.0, 70, false, 0, 'Простая броня из кожи.', NULL, true, 'body', 2),
('Кольчуга', 'Броня', 'Необычный', 0, 25, '{"strength": 3}', NULL, 12.0, 120, false, 0, 'Кольчуга для умеренной защиты.', NULL, true, 'body', 3),
('Пластины', 'Броня', 'Редкий', 0, 40, '{"endurance": 5}', NULL, 20.0, 200, false, 0, 'Тяжёлая броня для максимальной защиты.', NULL, true, 'body', 6),
('Шлем из стали', 'Броня', 'Необычный', 0, 20, '{"endurance": 3}', NULL, 5.0, 90, false, 0, 'Надёжная защита для головы.', NULL, true, 'helmet', 3),
('Сапоги разведчика', 'Броня', 'Редкий', 0, 10, '{"dexterity": 3}', NULL, 2.0, 75, false, 0, 'Удобные и лёгкие сапоги.', NULL, true, 'boots', 2),
('Мифриловый нагрудник', 'Броня', 'Легендарный', 0, 50, '{"endurance": 10}', NULL, 15.0, 500, false, 0, 'Броня из мифрила для максимальной защиты.', NULL, true, 'body', 7),
('Шлем мудреца', 'Броня', 'Эпический', 0, 15, '{"интеллект": 7}', NULL, 3.0, 300, false, 0, 'Шлем для тех, кто владеет магией.', NULL, true, 'helmet', 6),
('Кольчужные перчатки', 'Броня', 'Необычный', 0, 10, '{"strength": 2}', NULL, 2.0, 80, false, 0, 'Перчатки для дополнительной защиты.', NULL, true, 'gloves', 3),
-- Аксессуары
('Амулет удачи', 'Аксессуар', 'Редкий', 0, 0, '{"luck": 5}', NULL, 0.5, 75, false, 0, 'Амулет, повышающий удачу.', NULL, true, 'neck', 3),
('Плащ теней', 'Аксессуар', 'Эпический', 0, 0, '{"dexterity": 4}', NULL, 1.0, 200, false, 0, 'Плащ, улучшающий ловкость.', NULL, true, 'cloak', 5),
('Кулон мага', 'Аксессуар', 'Эпический', 0, 0, '{"intelligence": 6}', NULL, 0.6, 220, false, 0, 'Амулет для увеличения магической силы.', NULL, true, 'neck', 6),
('Амулет древних', 'Аксессуар', 'Легендарный', 0, 0, '{"intelligence": 8, "luck": 4}', NULL, 0.7, 300, false, 0, 'Мощный артефакт древних.', NULL, true, 'neck', 7);
    """)



    op.execute("""
               CREATE TABLE monsters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    health INT NOT NULL,
    attack INT NOT NULL,
    defense INT NOT NULL,
    strength INT,
    endurance INT,
    intelligence INT,
    dexterity INT,
    loot JSONB
);
""")

    op.execute("""
        INSERT INTO monsters (name, description, health, attack, defense, strength, endurance, intelligence, dexterity, loot)
VALUES
('Гоблин', 'Слабое и хитрое существо.', 300, 15, 5, 3, 2, 1, 5, '[{"item_id": 1, "quantity": 1, "drop_rate": 0.5}]'),
('Волк', 'Быстрый и свирепый хищник.', 500, 20, 10, 4, 3, 1, 8, '[{"item_id": 3, "quantity": 2, "drop_rate": 0.3}]'),
('Разбойник', 'Изгой, нападающий на слабых.', 700, 25, 15, 5, 4, 2, 6, '[{"item_id": 2, "quantity": 1, "drop_rate": 0.4}]'),
('Тролль', 'Крупный и мощный противник.', 1200, 50, 30, 8, 6, 1, 3, '[{"item_id": 4, "quantity": 1, "drop_rate": 0.2}]'),
('Скелет', 'Оживший мертвец.', 400, 20, 10, 3, 3, 1, 4, '[{"item_id": 5, "quantity": 1, "drop_rate": 0.5}]'),
('Гигантский паук', 'Опасный лесной хищник.', 600, 30, 15, 4, 4, 2, 10, '[{"item_id": 6, "quantity": 1, "drop_rate": 0.4}]'),
('Медведь', 'Массивный и сильный зверь.', 1000, 40, 25, 7, 5, 1, 6, '[{"item_id": 7, "quantity": 1, "drop_rate": 0.3}]'),
('Костяной маг', 'Скелет с магическими способностями.', 800, 35, 20, 5, 4, 6, 4, '[{"item_id": 8, "quantity": 1, "drop_rate": 0.2}]'),
('Огр', 'Сильный, но медлительный противник.', 1500, 60, 35, 9, 7, 2, 2, '[{"item_id": 9, "quantity": 1, "drop_rate": 0.1}]'),
('Вампир', 'Хитрый и опасный враг.', 900, 50, 20, 6, 5, 7, 7, '[{"item_id": 10, "quantity": 1, "drop_rate": 0.25}]');
    """)


def downgrade() -> None:
    op.execute("DROP TABLE monsters;")
