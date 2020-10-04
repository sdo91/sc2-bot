from sc2.unit import UnitTypeId, UnitOrder, AbilityId, Unit, BuffId
from math import sqrt, degrees, atan
from random import randint
from sc2.position import Point2


class ArmyManager:
    x_buffer = 26
    y_buffer = 26
    map_x_max = 192
    map_y_max = 154
    buffer_to_buffer = 1

    ai = None

    def __init__(self, ai):
        from bots.resonator_bot import ResonatorBot
        self.ai: ResonatorBot = ai
        self.sent_adept_wave = False

    @classmethod
    def calculate_vector_location(cls, unit, unit2, desired_distance):
        vector = (unit.position[0] - unit2.position[0],
                  unit.position[1] - unit2.position[1])
        current_distance = sqrt(vector[0] ** 2 + vector[1] ** 2)
        multiplication_factor = desired_distance / current_distance
        movement_vector = (multiplication_factor * vector[0], multiplication_factor * vector[1])
        point = Point2((unit.position[0] + movement_vector[0], unit.position[1] + movement_vector[1]))
        return point

    @classmethod
    def calculate_vector_using_point_location(cls, unit, point_2: Point2, desired_distance):
        vector = (unit.position[0] - point_2.x,
                  unit.position[1] - point_2.y)
        current_distance = sqrt(vector[0] ** 2 + vector[1] ** 2)
        multiplication_factor = desired_distance / current_distance
        movement_vector = (multiplication_factor * vector[0], multiplication_factor * vector[1])
        return Point2((unit.position[0] + movement_vector[0], unit.position[1] + movement_vector[1]))

    @classmethod
    def calculate_avoid_bottom_left_corner_vector(cls, point_1: Point2, desired_distance):
        if point_1.x < desired_distance + cls.x_buffer + cls.buffer_to_buffer and point_1.y < desired_distance + cls.y_buffer + cls.buffer_to_buffer:
            escape_angle = 90 - degrees(atan(point_1.x/point_1.y))
            percentage_x = escape_angle / 90.0
            percentage_y = 1 - percentage_x

            desired_x = percentage_x * (desired_distance + cls.x_buffer)
            desired_y = percentage_y * (desired_distance + cls.y_buffer)

            vector = (abs(0 - desired_x + cls.y_buffer), abs(0 - desired_y + cls.y_buffer))
            print("AVOID BOTTOM LEFT")

            return Point2(vector)

        else:
            return point_1

    def calculate_avoid_bottom_right_corner_vector(self, point_1: Point2, desired_distance):

        x_distance_from_corner = self.map_x_max - point_1.x
        if self.map_x_max - point_1.x < desired_distance + self.x_buffer + self.buffer_to_buffer and point_1.y < desired_distance + self.y_buffer + self.buffer_to_buffer:
            escape_angle = 90 - degrees(atan(x_distance_from_corner/point_1.y))
            percentage_x = escape_angle / 90.0
            percentage_y = 1 - percentage_x

            desired_x = percentage_x * (desired_distance + self.x_buffer)
            desired_y = percentage_y * (desired_distance + self.y_buffer)

            vector = (abs(self.map_x_max - (desired_x + self.x_buffer)), abs(0 - desired_y + self.y_buffer))
            print("AVOID BOTTOM RIGHT")

            return Point2(vector)

        else:
            return point_1

    def calculate_avoid_top_right_corner_vector(self, point_1: Point2, desired_distance):
        x_distance_from_corner = self.map_x_max - point_1.x
        y_distance_from_corner = self.map_y_max - point_1.y
        if x_distance_from_corner < desired_distance + self.x_buffer + self.buffer_to_buffer and y_distance_from_corner < desired_distance + self.y_buffer + self.buffer_to_buffer:
            escape_angle = 90 - degrees(atan(x_distance_from_corner/y_distance_from_corner))
            percentage_x = escape_angle / 90.0
            percentage_y = 1 - percentage_x

            desired_x = percentage_x * (desired_distance + self.x_buffer)
            desired_y = percentage_y * (desired_distance + self.y_buffer)

            vector = (abs(self.map_x_max - (desired_x + self.x_buffer)), abs(self.map_y_max - (desired_y + self.y_buffer)))
            print("AVOID TOP RIGHT")

            return Point2(vector)

        else:
            return point_1

    def calculate_avoid_wall(self, unit: UnitTypeId, point_1: Point2):
        adjacent = point_1.x
        opposite = point_1.y
        if point_1.y < self.y_buffer + self.buffer_to_buffer:
            opposite = self.y_buffer
            opposite_length = self.y_buffer - point_1.y

            hypotenuse = sqrt((unit.position[0] - point_1.x)**2 + (unit.position[1] - point_1.y)**2)

            adjacent = sqrt(abs(hypotenuse**2 - opposite_length**2))

            new_hyptenuse = adjacent**2 + self.y_buffer**2

        elif point_1.y > self.map_y_max - (self.y_buffer + self.buffer_to_buffer):

            opposite_length = point_1.y - self.map_y_max - self.y_buffer

            hypotenuse = sqrt((unit.position[0] - point_1.x)**2 + (unit.position[1] - point_1.y)**2)

            adjacent = sqrt(abs(hypotenuse**2 - opposite_length**2))

            new_hyptenuse = adjacent ** 2 + self.y_buffer ** 2

            opposite = self.map_y_max - self.y_buffer


        return Point2((adjacent, opposite))


    def calculate_avoid_top_left_corner_vector(self, point_1: Point2, desired_distance):

        x_distance_from_corner = self.map_x_max - point_1.x
        y_distance_from_corner = self.map_y_max - point_1.y
        if x_distance_from_corner < desired_distance + self.x_buffer + self.buffer_to_buffer and y_distance_from_corner < desired_distance + self.y_buffer + self.buffer_to_buffer:
            escape_angle = 90 - degrees(atan(x_distance_from_corner / y_distance_from_corner))
            percentage_x = escape_angle / 90
            percentage_y = 1 - percentage_x

            desired_x = percentage_x * (desired_distance + self.x_buffer)
            desired_y = percentage_y * (desired_distance + self.y_buffer)

            vector = (abs(self.map_x_max - desired_x + self.y_buffer), abs(self.map_y_max - (desired_y + self.y_buffer)))
            print("AVOID TOP LEFT")

            return Point2(vector)

        else:
            return point_1


    def do_attack(self):
        self.map_x_max = self.ai.game_info.map_size[0]
        self.map_y_max = self.ai.game_info.map_size[1]

        self.ai.distance_to_enemy_base = (
                abs(self.ai.start_location.position[0] - self.ai.enemy_start_locations[0].position[0]) + (
                self.ai.start_location.position[1] - self.ai.enemy_start_locations[0].position[1]))

        number_of_adepts_at_base = self.ai.units(UnitTypeId.ADEPT).further_than(self.ai.distance_to_enemy_base / 2,
                                                                                self.ai.enemy_start_locations[
                                                                                    0].position)

        number_of_adepts_away = self.ai.units(UnitTypeId.ADEPT).closer_than(self.ai.distance_to_enemy_base / 2,
                                                                            self.ai.enemy_start_locations[0].position)


        enemy_combat_units = self.ai.enemy_units.exclude_type \
            ([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *self.ai.building_id_list, UnitTypeId.OVERLORD,
              UnitTypeId.MEDIVAC, UnitTypeId.LARVA, UnitTypeId.BANELINGCOCOON, UnitTypeId.EGG, UnitTypeId.OVERSEER])
        enemy_anti_air_buildings = self.ai.enemy_structures.of_type([UnitTypeId.SPORECRAWLER, UnitTypeId.MISSILETURRET, UnitTypeId.PHOTONCANNON])
        enemy_anti_air_combat_units = self.ai.enemy_units.of_type(self.ai.enemy_anti_air_types)
        enemy_anti_air_combat_units += enemy_anti_air_buildings
        enemy_expansions = self.ai.enemy_structures.of_type(self.ai.expansion_types)

        enemy_workers = self.ai.enemy_units(self.ai.enemy_worker_type)
        enemy_mineral_field = self.ai.mineral_field.closest_to(self.ai.enemy_start_locations[0])

        enemy_units_attacking_us = enemy_combat_units.closer_than(self.ai.distance_to_enemy_base/3, self.ai.start_location)
        oracles = self.ai.units(UnitTypeId.ORACLE)
        phoenixes = self.ai.units(UnitTypeId.PHOENIX)



        if enemy_units_attacking_us.amount > (1 + number_of_adepts_at_base.amount):
          for worker in self.ai.workers:
              worker.attack(enemy_units_attacking_us.closest_to(worker).position)


        for phoenix in phoenixes:
            closest_anti_air_enemy = None
            close_anti_air = []
            if enemy_anti_air_combat_units:
                closest_anti_air_enemy = enemy_anti_air_combat_units.closest_to(phoenix.position)
                close_anti_air = enemy_anti_air_combat_units.closer_than(12, phoenix.position)

            if close_anti_air:
                if phoenix.shield_percentage < 0.3 and phoenix.is_using_ability(AbilityId.GRAVITONBEAM_GRAVITONBEAM):
                    phoenix(AbilityId.CANCEL_GRAVITONBEAM)

                if close_anti_air.amount >= phoenixes.closer_than(5, phoenix).amount:
                    if phoenix.is_using_ability(AbilityId.GRAVITONBEAM_GRAVITONBEAM):
                        phoenix(AbilityId.CANCEL_GRAVITONBEAM)
                    point = self.calculate_vector_location(phoenix, closest_anti_air_enemy, 10)
                    point = self.calculate_avoid_wall(unit=phoenix, point_1=point)
                    if close_anti_air.of_type([UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR]):
                        point = self.calculate_avoid_bottom_left_corner_vector(point, 4)
                        point = self.calculate_avoid_bottom_right_corner_vector(point, 4)
                        point = self.calculate_avoid_top_right_corner_vector(point, 4)
                        point = self.calculate_avoid_top_left_corner_vector(point, 4)
                    phoenix.move(point)
                else:
                    if not enemy_anti_air_buildings.closer_than(8, phoenix):
                        if phoenix.shield_percentage > 0.5:
                            if phoenix.energy > 50:
                                phoenix(AbilityId.GRAVITONBEAM_GRAVITONBEAM, close_anti_air[0])

                            for ally in phoenixes.closer_than(10, phoenix):
                                if ally.is_using_ability([AbilityId.GRAVITONBEAM_GRAVITONBEAM]):
                                    phoenix.move(ally)
                                break
            else:
                enemy_defenseless_air = self.ai.enemy_units.of_type([UnitTypeId.OVERLORD, UnitTypeId.OVERSEER])
                if enemy_defenseless_air:
                    closest_defenseless_air = enemy_defenseless_air.closest_to(phoenix.position)
                    phoenix.move(closest_defenseless_air.position)
                else:
                    if not hasattr(phoenix, 'location_expansion'):
                        phoenix.location_expansion = self.ai.expansion_locations_list[randint(0, len(self.ai.expansion_locations_list) - 1)]
                        phoenix.move(enemy_mineral_field)
                    else:
                        phoenix.move(phoenix.location_expansion)

        for voidray in self.ai.units(UnitTypeId.VOIDRAY):
            print(voidray.position)
            close_anti_air = []
            closest_anti_air_enemy = None
            if enemy_workers:
                closest_anti_air_enemy = enemy_workers.closest_to(voidray.position)
                close_anti_air = enemy_workers.closer_than(11, voidray.position)

            if close_anti_air:
                point = self.calculate_vector_location(voidray, closest_anti_air_enemy, 10)
                point = self.calculate_avoid_wall(unit=voidray, point_1=point)
                if close_anti_air:
                    point = self.calculate_avoid_bottom_left_corner_vector(point, 4)
                    point = self.calculate_avoid_bottom_right_corner_vector(point, 4)
                    point = self.calculate_avoid_top_right_corner_vector(point, 4)
                    point = self.calculate_avoid_top_left_corner_vector(point, 4)
                print(point)

        def oracle_attack(oracl: Unit, close_anti_air):
            closest_enemy_building = None
            if self.ai.enemy_structures:
                closest_enemy_building = self.ai.enemy_structures.closest_to(oracle.position)
            if enemy_workers:
                oracl.move(enemy_workers.closest_to(oracl).position)
                close_workers = enemy_workers.closer_than(oracl.ground_range, oracl.position)
                if close_workers:
                    closest_worker = close_workers.closest_to(oracl.position)
                    if oracle.weapon_cooldown > 0.1:
                        oracle.move(closest_worker.position)
                    else:
                        oracl.attack(closest_worker)
                    if oracle.energy > 30:
                        oracl(AbilityId.BEHAVIOR_PULSARBEAMON)
            else:
                if oracle.has_buff(BuffId.ORACLEWEAPON):
                    if close_anti_air:
                        close_ground_anti_air = close_anti_air.exclude_type([UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR])
                        if close_ground_anti_air:
                            oracle.attack(close_ground_anti_air[0])
                    oracle.attack(closest_enemy_building)
                else:
                    if closest_enemy_building or close_anti_air and oracle.energy > 100:
                        oracle(AbilityId.BEHAVIOR_PULSARBEAMON)

                    if not hasattr(oracle, 'enemy_expansion'):
                        if enemy_expansions:
                            if enemy_expansions:
                                oracle.enemy_expansion = enemy_expansions[randint(0, len(enemy_expansions) - 1)]
                        oracl.move(enemy_mineral_field.position)
                    else:
                        oracle.move(oracle.enemy_expansion.position)

        for oracle in oracles:
            closest_anti_air_enemy = None
            close_anti_air = []
            if enemy_anti_air_combat_units:
                closest_anti_air_enemy = enemy_anti_air_combat_units.closest_to(oracle.position)
                close_anti_air = enemy_anti_air_combat_units.closer_than(12, oracle.position)

            if close_anti_air:
                if len(close_anti_air) + 3 > len(oracles.closer_than(12, oracle.position)):
                    point = self.calculate_vector_location(oracle, closest_anti_air_enemy, 40)
                    point = self.calculate_avoid_wall(unit=oracle, point_1=point)
                    if close_anti_air.of_type([UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR]):
                        point = self.calculate_avoid_bottom_left_corner_vector(point, 4)
                        point = self.calculate_avoid_bottom_right_corner_vector(point, 4)
                        point = self.calculate_avoid_top_right_corner_vector(point, 4)
                        point = self.calculate_avoid_top_left_corner_vector(point, 4)
                    oracle.move(point)
                else:
                    oracle_attack(oracle, close_anti_air)
            else:
                oracle_attack(oracle, close_anti_air)

        for unit in number_of_adepts_at_base:
            if number_of_adepts_at_base.amount >= self.ai.wave_amount:
                unit.attack(self.ai.enemy_start_locations[0])

                if not self.sent_adept_wave:
                    self.sent_adept_wave = True
                    print("sent first adept wave at t={}".format(self.ai.time_formatted))
            elif enemy_units_attacking_us:
                closest_enemy = enemy_units_attacking_us.closest_to(unit)
                if unit.weapon_cooldown > 0.08 and unit.shield_percentage < 0.3:
                    unit.move(self.calculate_vector_location(unit, closest_enemy, unit.movement_speed))
                else:
                    unit.attack(closest_enemy)


        for unit in number_of_adepts_away:
            closest_non_worker_enemy = self.ai.closest_enemy_combat_unit(unit)

            if enemy_workers:
                probes_within_attack_range = enemy_workers.closer_than(unit.ground_range, unit.position)
                if probes_within_attack_range:
                    for probe in probes_within_attack_range:
                        if probe.shield_health_percentage < 1:
                            unit.attack(probe)
                            break
                if closest_non_worker_enemy:
                    if enemy_combat_units.closer_than(unit.ground_range + 2.0, unit):
                        unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, unit.position)

                        if unit.weapon_cooldown > 0.08:
                            unit.move(
                                self.calculate_vector_location(unit, closest_non_worker_enemy, unit.movement_speed))
                    else:
                        unit.attack(enemy_workers.closest_to(unit.position))

            else:
                if closest_non_worker_enemy:
                    if enemy_combat_units.closer_than(unit.ground_range + 8.0,
                                                      unit) or unit.in_ability_cast_range(
                        AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, enemy_mineral_field.position):
                        unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, unit.position)
                        unit.attack(enemy_mineral_field.position)

                    if unit.weapon_cooldown > 0.08:
                        unit.move(self.calculate_vector_location(unit, closest_non_worker_enemy, unit.movement_speed))
                    else:
                        unit.attack(enemy_mineral_field.position)

                else:
                    if not enemy_combat_units:
                        enemy_buildings = self.ai.enemy_structures()
                        if enemy_buildings:
                            closest_building = enemy_buildings.closest_to(unit.position)
                            unit.attack(closest_building)

        phase_shifts = self.ai.units(UnitTypeId.ADEPTPHASESHIFT)
        for phase_shift in phase_shifts:
            closest_enemy = self.ai.closest_enemy_combat_unit(phase_shift)

            if closest_enemy:
                closest_enemy: Unit
                if enemy_workers:
                    phase_shift.move(enemy_workers.furthest_to(closest_enemy.position))
                else:
                    if enemy_expansions:
                        phase_shift.move(enemy_expansions.furthest_to(closest_enemy.position))
                    else:
                        phase_shift.move(enemy_mineral_field.position)

                if len(self.ai.enemy_units.closer_than(closest_enemy.ground_range, phase_shift.position)) > len \
                            (self.ai.units.closer_than(5,
                                                       phase_shift.position)) and phase_shift.buff_duration_remain < 8:
                    phase_shift(AbilityId.CANCEL_ADEPTSHADEPHASESHIFT)

            else:
                if enemy_workers:
                    phase_shift.move(enemy_workers.closest_to(phase_shift.position))
                else:
                    if enemy_expansions:
                        phase_shift.move(enemy_expansions.closest_to(phase_shift.position))
                    else:
                        phase_shift.move(enemy_mineral_field.position)
