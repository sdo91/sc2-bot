from sc2.unit import UnitTypeId, UnitOrder, AbilityId, Unit, BuffId
from math import sqrt
from sc2.position import Point2


class ArmyManager:

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
        return Point2((unit.position[0] + movement_vector[0], unit.position[1] + movement_vector[1]))

    def do_attack(self):

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
              UnitTypeId.MEDIVAC])
        enemy_anti_air_buildings = self.ai.enemy_structures(UnitTypeId.SPORECRAWLER, UnitTypeId.MISSILETURRET, UnitTypeId.PHOTONCANNON)
        enemy_anti_air_combat_units = self.ai.enemy_units.of_type(self.ai.enemy_anti_air_types)
        enemy_anti_air_combat_units += enemy_anti_air_buildings
        enemy_expansions = self.ai.enemy_structures.of_type(self.ai.expansion_types)

        enemy_workers = self.ai.enemy_units(self.ai.enemy_worker_type)
        enemy_mineral_field = self.ai.mineral_field.closest_to(self.ai.enemy_start_locations[0])
        oracles = self.ai.units(UnitTypeId.ORACLE)

        def oracle_attack(oracl: Unit):
            if enemy_workers:
                oracl.move(enemy_workers.closest_to(oracl).position)
                close_workers = enemy_workers.closer_than(oracl.ground_range, oracl.position)
                if close_workers:
                    oracl.attack(close_workers.closest_to(oracl.position).position)
                    if oracle.energy > 30:
                        oracl(AbilityId.BEHAVIOR_PULSARBEAMON)
            else:
                oracl.move(enemy_mineral_field.position)

        for oracle in oracles:
            closest_anti_air_enemy = None
            close_anti_air = []
            if enemy_anti_air_combat_units:
                closest_anti_air_enemy = enemy_anti_air_combat_units.closest_to(oracle.position)
                close_anti_air = enemy_anti_air_combat_units.closer_than(10, oracle.position)

            if close_anti_air:
                if len(close_anti_air) + 3 > len(oracles.closer_than(10, oracle.position)):
                    oracle.move(self.calculate_vector_location(oracle, closest_anti_air_enemy, 10))
                else:
                    oracle_attack(oracle)
            else:
                oracle_attack(oracle)

        for unit in number_of_adepts_at_base:
            if number_of_adepts_at_base.amount >= self.ai.wave_amount:
                unit.attack(self.ai.enemy_start_locations[0])

                if not self.sent_adept_wave:
                    self.sent_adept_wave = True
                    print("sent first adept wave at t={}".format(self.ai.time_formatted))

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
                        enemy_buildings = self.ai.enemy_structures
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
