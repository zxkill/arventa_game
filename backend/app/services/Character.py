import json
import random
import time

from loguru import logger

from app.config.config import redis


class Character:
    DEFAULT_STATS = {
        'health': 600,  # очки здоровья
        'recovery_health': 120,  # восстановление здоровья в минуту
        'energy': 60,  # очки энергии
        'recovery_energy': 12,  # восстановление энергии в минуту
        'weight': 50,  # максимальный вес
        'attack': 10,  # базовая атака
        'defense': 5,  # базовая защита
        'accuracy': 0,  # точность
        'evasion': 0,  # уклонение
        'speed': 10  # скорость
    }
    STATE_REDIS_TTL = 600

    def __init__(self, character_data, items_data=None, character_type='player'):
        self.character_data = character_data
        self.state_key_redis = f"character.state:{character_type}:{self.character_data['id']}"
        self.items_data = items_data
        self.items_attribute = self.get_items_attribute()
        self.state = self.get_character_state()

    def get_max_health(self):
        # Max_HP = 100 + (Выносливость * 10)
        if self.character_data.get('health'):
            health = self.character_data.get('health')
        else:
            health = self.DEFAULT_STATS['health']
        health = health + (self.get_endurance() * 10)
        return health

    def get_cur_health(self):
        logger.debug(f"cur health: {self.state['health']}")
        return int(self.state['health'])

    def get_recovery_health(self):
        health = self.DEFAULT_STATS['recovery_health']
        return health

    def get_max_energy(self):
        # Max_MP = 50 + (Интеллект * 5)
        if self.character_data.get('energy'):
            energy = self.character_data.get('energy')
        else:
            energy = self.DEFAULT_STATS['energy']
        energy = energy + (self.get_intelligence() * 5)
        return energy

    def get_cur_energy(self):
        return int(self.state['energy'])

    def get_recovery_energy(self):
        return self.DEFAULT_STATS['recovery_energy']

    def get_max_weight(self):
        if self.character_data.get('weight'):
            weight = self.character_data.get('weight') + self.items_attribute['max_weight']
        else:
            weight = self.DEFAULT_STATS['weight'] + self.items_attribute['max_weight']
        return weight

    def get_cur_weight(self):
        return self.items_attribute['weight']

    def get_attack(self):
        # Damage = (Base_Attack + Weapon_Attack) * (1 + Strength / 100) * (1 + Crit_Chance / 100)
        # Magic_Damage = (Base_Magic_Power + Weapon_Magic_Power) * (1 + Intelligence / 100)
        if self.character_data.get('attack'):
            attack = self.character_data.get('attack')
        else:
            attack = self.DEFAULT_STATS['attack']
        return (
                (attack + self.items_attribute['damage'])
                * (1 + self.get_strength() / 100)
                * (1 + self.get_crit_chance() / 100))

    def get_defense(self):
        # Total_Defense = Base_Defense + Armor_Defense + (Endurance * 2)
        if self.character_data.get('defense'):
            defense = self.character_data.get('defense')
        else:
            defense = self.DEFAULT_STATS['defense']
        return defense + self.items_attribute['armor'] + (self.get_endurance() * 2)

    def get_crit_chance(self):
        # Crit_Chance = 5% + (Luck / 10)
        return ((5 * (self.get_luck() / 10)) / 100) + (self.get_luck() / 10)

    def get_evasion_chance(self):
        # шанс уклонения
        # Evasion_Chance = Base_Speed + (Dexterity / 2) - Opponent_Accuracy
        if self.character_data.get('evasion'):
            evasion = self.character_data.get('evasion')
        else:
            evasion = self.DEFAULT_STATS['evasion']
        return evasion + (self.get_dexterity() / 2)

    def get_speed(self):
        if self.character_data.get('speed'):
            speed = self.character_data.get('speed')
        else:
            speed = self.DEFAULT_STATS['speed']
        return speed + self.items_attribute.get('speed', 0)

    def get_strength(self):
        return self.items_attribute['strength']

    def get_dexterity(self):
        return self.items_attribute['dexterity']

    def get_intelligence(self):
        return self.items_attribute['intelligence']

    def get_endurance(self):
        return self.items_attribute['endurance']

    def get_luck(self):
        return self.items_attribute['luck']

    def get_accuracy(self):
        if self.character_data.get('accuracy'):
            accuracy = self.character_data.get('accuracy')
        else:
            accuracy = self.DEFAULT_STATS['accuracy']
        return accuracy + self.items_attribute.get('accuracy', 0)

    def get_loot(self):
        return self.character_data['loot']

    def get_items_attribute(self):
        weight = 0.0
        max_weight = 0.0
        damage = 0
        armor = 0
        endurance = 0
        intelligence = 0
        strength = 0
        dexterity = 0
        luck = 0
        accuracy = 0
        speed = 0
        if self.items_data:
            for item_data in self.items_data:
                weight += (item_data['weight'] * item_data['quantity'])
                logger.debug(f"Item data in users helper {item_data}")
                if item_data['is_equipped']:
                    damage += item_data.get("damage", 0)
                    armor += item_data.get("armor", 0)
                    if item_data.get("effect_original"):
                        effects = json.loads(item_data.get("effect_original"))
                        if effects:
                            endurance += effects.get("endurance", 0)
                            intelligence += effects.get("intelligence", 0)
                            strength += effects.get("strength", 0)
                            dexterity += effects.get("dexterity", 0)
                            luck += effects.get("luck", 0)
                            accuracy += effects.get("accuracy", 0)
                            speed += effects.get("speed", 0)
                            max_weight += effects.get("max_weight", 0)

        return {
            'weight': weight,
            'max_weight': max_weight,
            'damage': damage,
            'armor': armor,
            'endurance': endurance,
            'intelligence': intelligence,
            'strength': strength,
            'dexterity': dexterity,
            'luck': luck,
            'accuracy': accuracy,
            'speed': speed
        }

    def get_attributes(self):
        return {
            'max_health': round(self.get_max_health()),
            'cur_health': round(self.get_cur_health()),
            'recovery_health': round(self.get_recovery_health()),
            'max_energy': round(self.get_max_energy()),
            'cur_energy': round(self.get_cur_energy()),
            'recovery_energy': round(self.get_recovery_energy()),
            'max_weight': round(self.get_max_weight(), 2),
            'cur_weight': round(self.get_cur_weight(), 2),
            'attack': round(self.get_attack(), 1),
            'defense': round(self.get_defense(), 1),
            'crit_chance': round(self.get_crit_chance(), 1),
            'evasion_chance': round(self.get_evasion_chance(), 1),

            'strength': round(self.get_strength()),
            'dexterity': round(self.get_dexterity()),
            'intelligence': round(self.get_intelligence()),
            'endurance': round(self.get_endurance()),
            'luck': round(self.get_luck()),
            'speed': round(self.get_speed()),
            'accuracy': round(self.get_accuracy()),

            'last_updated': self.state['last_updated'],
        }

    def calculate_current_state(self):
        data = redis.hgetall(self.state_key_redis)
        if not data:
            logger.debug("Character not found in Redis.")
            return None

        current_time = int(time.time())
        last_updated = int(data["last_updated"])
        elapsed_seconds = (current_time - last_updated)  # Время в секундах

        # Расчёт здоровья
        current_health = min(
            int(data["health"]) + elapsed_seconds * int((int(data["recovery_rate_health"]) / 60)),
            int(data["max_health"])
        )

        # Расчёт энергии
        current_energy = min(
            int(data["energy"]) + elapsed_seconds * int((int(data["recovery_rate_energy"]) / 60)),
            int(data["max_energy"])
        )

        # Обновляем в Redis
        updated_data = {
            "health": int(current_health),
            "energy": int(current_energy),
            "last_updated": int(current_time)
        }
        redis.hset(self.state_key_redis, mapping=updated_data)

        logger.debug(f"Character {self.character_data['id']} state updated.")
        return {"health": current_health, "energy": current_energy}

    # создаем запись в редис
    def create_character_in_redis(self):
        logger.debug(f"Зашли в метод create_character_in_redis")
        logger.debug(f"key: {self.state_key_redis}")
        character_data = {
            "health": self.get_max_health(),
            "energy": self.get_max_energy(),
            "last_updated": int(time.time()),  # Текущее время в секундах
            "recovery_rate_health": self.get_recovery_health(),  # Восстановление здоровья за минуту
            "recovery_rate_energy": self.get_recovery_energy(),  # Восстановление энергии за минуту
            "max_health": self.get_max_health(),
            "max_energy": self.get_max_energy(),
        }
        logger.debug(f"Character data {character_data}")
        redis.hset(self.state_key_redis, mapping=character_data)
        redis.expire(self.state_key_redis, self.STATE_REDIS_TTL)
        logger.debug(f"Character {self.character_data['id']} created in Redis.")

    # обработка урона
    def take_damage(self, damage, opponent_accuracy):
        if self.attempt_evasion(opponent_accuracy):
            logger.debug(f"{self.character_data['id']} уклонился от атаки!")
            return False

        data = self.calculate_current_state()
        if not data:
            return False

        current_health = int(max(0, data["health"] - damage))
        redis.hset(self.state_key_redis, "health", current_health)
        self.state = self.get_character_state()
        logger.debug(f"{self.character_data['id']} нанес {damage} урона. Здоровье теперь {current_health}.")
        return True


    def attempt_evasion(self, opponent_accuracy):
        evasion_chance = self.get_evasion_chance() - opponent_accuracy
        roll = random.uniform(0, 100)
        return roll < evasion_chance

    def get_character_state(self):
        logger.debug('Зашли в метод get_character_state')
        data = self.calculate_current_state()  # Пересчёт перед выдачей данных
        logger.debug(f"Character data in get_character_state {data}")
        if not data:
            self.create_character_in_redis()
        logger.debug(f"health={redis.hget(self.state_key_redis, "health")}")
        logger.debug(f"energy={redis.hget(self.state_key_redis, "energy")}")
        logger.debug(f"last_updated={redis.hget(self.state_key_redis, "last_updated")}")
        return {
            "health": redis.hget(self.state_key_redis, "health"),
            "energy": redis.hget(self.state_key_redis, "energy"),
            "last_updated": redis.hget(self.state_key_redis, "last_updated")
        }

    def reset_character_state(self):
        redis.delete(self.state_key_redis)