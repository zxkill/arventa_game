import random

from app.services.Character import Character


# Функция расчета урона
def calculate_damage(attacker: Character, defender: Character):
    # Проверка попадания
    damage = max(0, attacker.get_attack() - defender.get_defense()) * random.uniform(0.85, 1.15)
    # Проверка критического удара
    if random.random() < attacker.get_crit_chance():
        damage *= 2 # критический урон увеличиваем в два раза todo потом сделаем расчет
        critical = True
    else:
        critical = False
    return int(damage), critical


class Skill:
    def __init__(self, name, damage, mana_cost, effect=None):
        self.name = name
        self.damage = damage
        self.mana_cost = mana_cost
        self.effect = effect  # Example: {"type": "burn", "duration": 3, "damage_per_turn": 5}

    def apply_effect(self, target):
        if self.effect:
            target.effects.append(self.effect)


# Расчёт действия навыка
fireball = Skill("Fireball", damage=20, mana_cost=10, effect={"type": "burn", "duration": 3, "damage_per_turn": 5})
# fireball.apply_effect(enemy)
