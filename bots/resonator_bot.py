import os
import sys
from math import sqrt
from typing import Union

from bots.structure_manager import StructureManager

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sc2
from sc2 import Race, Difficulty
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.units import Units, Unit

zerg_building_list = [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.SPAWNINGPOOL,
                      UnitTypeId.EVOLUTIONCHAMBER, UnitTypeId.SPIRE]

protoss_building_list = [UnitTypeId.PYLON, UnitTypeId.GATEWAY, UnitTypeId.STARGATE, UnitTypeId.ROBOTICSFACILITY,
                         UnitTypeId.ROBOTICSBAY, UnitTypeId.ASSIMILATOR]
terran_building_list = [UnitTypeId.COMMANDCENTER, UnitTypeId.COMMANDCENTERFLYING, UnitTypeId.ORBITALCOMMAND,
                        UnitTypeId.ORBITALCOMMANDFLYING, UnitTypeId.PLANETARYFORTRESS, UnitTypeId.BARRACKS,
                        UnitTypeId.BARRACKSFLYING, UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKSTECHLAB,
                        UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING, UnitTypeId.FACTORYREACTOR,
                        UnitTypeId.FACTORYTECHLAB, UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING,
                        UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORTTECHLAB, UnitTypeId.SUPPLYDEPOT,
                        UnitTypeId.ENGINEERINGBAY, UnitTypeId.ARMORY]
expansion_types = [UnitTypeId.NEXUS, UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS]
building_id_list = zerg_building_list

enemy_worker_type = UnitTypeId.DRONE
enemy_race = Race.Protoss



if enemy_race == Race.Zerg:
    building_id_list = zerg_building_list
    enemy_worker_type = UnitTypeId.DRONE
elif enemy_race == Race.Terran:
    building_id_list = terran_building_list
    enemy_worker_type = UnitTypeId.SCV
else:
    building_id_list = protoss_building_list
    enemy_worker_type = UnitTypeId.PROBE




class ResonatorBot(sc2.BotAI):

    def closest_enemy_combat_unit(self, unitv):
        if self.non_worker_enemies:
            return self.non_worker_enemies.closest_to(unitv.position)
        else:
            return False
    """
    todo:
        build different unit types
            stargates/oracle
        do something else with chronoboost after glaives are done
        use tech_requirement_progress method?
        search code for more todos

        add build order logic
            eg: cybercore: gateway, 200m, 15 probes
    """

    def __init__(self):
        super().__init__()

        self.structure_manager = StructureManager(self)

        self.PROBES_PER_BASE = 16 + 6

        self.save_minerals = False
        self.save_vespene = False

        self.distance_to_enemy_base = 100
        self.wave_amount = 6
        self.sent_adept_wave = False
        self.bulding_for_rally = None
        self.non_worker_enemies: ['Units'] = None

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        print("{} upgrade complete @ {}".format(upgrade, self.time_formatted))

    async def on_building_construction_complete(self, unit: Unit):
        print("building {} complete @ {}".format(unit, self.time_formatted))
        if unit.type_id == UnitTypeId.GATEWAY:
            unit(AbilityId.RALLY_BUILDING, self.start_location.towards(self.game_info.map_center, 15))


    def can_afford(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId], check_supply_cost: bool = True) -> bool:
        cost = self.calculate_cost(item_id)
        if cost.minerals > 0 and self.save_minerals:
            # a higher priority task is waiting for minerals
            return False
        if cost.vespene > 0 and self.save_vespene:
            # a higher priority task is waiting for minerals
            return False
        return super().can_afford(item_id, check_supply_cost)

    def save_for(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId]):
        cost = self.calculate_cost(item_id)
        if cost.minerals > 0:
            self.save_minerals = True
        if cost.vespene > 0:
            self.save_vespene = True

    async def on_step(self, iteration):
        """
        called every frame (~24 fps)
        """
        self.bulding_for_rally = self.structures[0]
        self.save_minerals = False
        self.save_vespene = False
        self.non_worker_enemies = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *building_id_list, UnitTypeId.OVERLORD, UnitTypeId.MEDIVAC])

        if iteration == 0:
            await self.chat_send("todo: add trash talk here")

        if not self.townhalls:
            # todo: improve this logic
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return
        else:
            nexus = self.townhalls.random

        # order these by priority

        self.make_probes(nexus, 16)

        await self.structure_manager.build_pylon()

        await self.structure_manager.build_gateways(nexus, 1, save=True)

        self.structure_manager.build_assimilators(nexus, 1)
        self.make_probes(nexus, 16 + 3)

        self.structure_manager.build_assimilators(nexus, 2)
        self.make_probes(nexus, 16 + 6)

        await self.structure_manager.expand()

        if self.structures(UnitTypeId.GATEWAY).ready:
            await self.structure_manager.build_structure(UnitTypeId.CYBERNETICSCORE, nexus)
            await self.structure_manager.build_gateways(nexus, 2)

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            await self.structure_manager.build_structure(UnitTypeId.TWILIGHTCOUNCIL, nexus)
            self.do_research(UnitTypeId.CYBERNETICSCORE, UpgradeId.WARPGATERESEARCH)
            self.make_army()
            await self.structure_manager.build_gateways(nexus, 4)

        if self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount > 0:
            self.structure_manager.build_assimilators(nexus, 2)
            self.make_probes(nexus, 16 + 3 + 3)
            await self.structure_manager.build_structure(UnitTypeId.STARGATE, nexus)

        self.do_chronoboost(nexus)

        self.do_research(UnitTypeId.TWILIGHTCOUNCIL, UpgradeId.ADEPTPIERCINGATTACK)

        self.do_attack()

        await self.distribute_workers()

        self.structure_manager.check_duplicate_structures()

    def make_probes(self, nexus, cap):
        # Make probes until we have enough
        if self.supply_workers < cap and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)
            else:
                self.save_for(UnitTypeId.PROBE)

    def do_chronoboost(self, nexus):
        if nexus.energy < 50:
            return  # not enough

        if not self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not nexus.is_idle:
                print("boosting nexus")
                nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
        else:
            tc = self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
            if not tc.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not tc.is_idle:
                print("boosting twilight council")
                nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, tc)

    def do_research(self, struct_id, upgrade_id):
        if self.already_pending_upgrade(upgrade_id):
            return
        if not self.structures(struct_id).ready:
            return
        if self.can_afford(upgrade_id):
            structure = self.structures(struct_id).ready.first
            structure.research(upgrade_id)
            print("started {} research @ {}".format(upgrade_id, self.time_formatted))
        else:
            self.save_for(upgrade_id)

    def make_army(self):
        self.make_unit(UnitTypeId.ADEPT)
        self.make_unit(UnitTypeId.ORACLE)

    def make_unit(self, unit_id):
        if self.tech_requirement_progress(unit_id) < 1:
            return
        if not self.can_afford(unit_id):
            return
        self.train(unit_id, train_only_idle_buildings=True)

    def do_attack(self):

        self.distance_to_enemy_base = (
                    abs(self.start_location.position[0] - self.enemy_start_locations[0].position[0]) + (
                        self.start_location.position[1] - self.enemy_start_locations[0].position[1]))

        number_of_adepts_at_base = self.units(UnitTypeId.ADEPT).further_than(self.distance_to_enemy_base / 2,
                                                                             self.enemy_start_locations[0].position)

        number_of_adepts_away = self.units(UnitTypeId.ADEPT).closer_than(self.distance_to_enemy_base / 2,
                                                                         self.enemy_start_locations[0].position)

        enemy_combat_units = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *building_id_list, UnitTypeId.OVERLORD, UnitTypeId.MEDIVAC])
        enemy_expansions = self.enemy_structures.of_type(expansion_types)

        probes = self.enemy_units(enemy_worker_type)
        enemy_mineral_field = self.mineral_field.closest_to(self.enemy_start_locations[0])


        for unit in number_of_adepts_at_base:
            if number_of_adepts_at_base.amount >= self.wave_amount:
                unit.attack(self.enemy_start_locations[0])

            if not self.sent_adept_wave:
                self.sent_adept_wave = True
                print("sent first adept wave at t={}".format(self.time_formatted))

        for unit in number_of_adepts_away:
            closest_non_worker_enemy = self.closest_enemy_combat_unit(unit)

            if probes:
                probes_within_attack_range = probes.closer_than(unit.ground_range, unit.position)
                if probes_within_attack_range:
                    for probe in probes_within_attack_range:
                        if probe.shield_health_percentage < 1:
                            unit.attack(probe)
                            break
                if closest_non_worker_enemy:
                    if enemy_combat_units.closer_than(unit.ground_range + 3.0, unit):
                        unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, unit.position)

                        if unit.weapon_cooldown > 0.1:
                            desired_distance = unit.movement_speed
                            vector = (unit.position[0] - closest_non_worker_enemy.position[0],
                                      unit.position[1] - closest_non_worker_enemy.position[1])
                            current_distance = sqrt(vector[0] ** 2 + vector[1] ** 2)
                            multiplication_factor = desired_distance / current_distance
                            movement_vector = (multiplication_factor * vector[0], multiplication_factor * vector[1])
                            unit.move(
                                Point2((unit.position[0] + movement_vector[0], unit.position[1] + movement_vector[1])))
                    else:
                        unit.attack(probes.closest_to(unit.position))

            else:
                if closest_non_worker_enemy:
                    if enemy_combat_units.closer_than(unit.ground_range + 8.0,
                                          unit) or unit.in_ability_cast_range(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, enemy_mineral_field.position):

                        unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, unit.position)
                        unit.attack(enemy_mineral_field.position)

                    if unit.weapon_cooldown > 0.1:
                        desired_distance = unit.movement_speed
                        vector = (unit.position[0] - closest_non_worker_enemy.position[0],
                                  unit.position[1] - closest_non_worker_enemy.position[1])
                        current_distance = sqrt(vector[0] ** 2 + vector[1] ** 2)
                        multiplication_factor = desired_distance / current_distance
                        movement_vector = (multiplication_factor * vector[0], multiplication_factor * vector[1])
                        unit.move(
                            Point2((unit.position[0] + movement_vector[0], unit.position[1] + movement_vector[1])))
                    else:
                        unit.attack(enemy_mineral_field.position)

                else:
                    if not enemy_combat_units:
                        enemy_buildings = self.enemy_structures
                        if enemy_buildings:
                            closest_building = enemy_buildings.closest_to(unit.position)
                            unit.attack(closest_building)

        phase_shifts = self.units(UnitTypeId.ADEPTPHASESHIFT)
        for phase_shift in phase_shifts:
            closest_enemy = self.closest_enemy_combat_unit(phase_shift)

            if closest_enemy:
                closest_enemy: Unit
                if probes:
                    phase_shift.move(probes.furthest_to(closest_enemy.position))
                else:
                    if enemy_expansions:
                        phase_shift.move(enemy_expansions.furthest_to(closest_enemy.position))
                    else:
                        phase_shift.move(enemy_mineral_field.position)

                if len(self.enemy_units.closer_than(closest_enemy.ground_range, phase_shift.position)) > len(self.units.closer_than(5, phase_shift.position)) and phase_shift.buff_duration_remain < 10:
                    phase_shift(AbilityId.CANCEL_ADEPTSHADEPHASESHIFT)

            else:
                if probes:
                    phase_shift.move(probes.closest_to(phase_shift.position))
                else:
                    if enemy_expansions:
                        phase_shift.move(enemy_expansions.closest_to(phase_shift.position))
                    else:
                        phase_shift.move(enemy_mineral_field.position)


def main():
    Difficulty_Easy = Difficulty.Easy
    Difficulty_Medium = Difficulty.Medium
    Difficulty_Hard = Difficulty.Hard
    Difficulty_VeryHard = Difficulty.VeryHard

    # computer = Computer(Race.Zerg, Difficulty_Medium)
    # computer = Computer(Race.Terran, Difficulty_Medium)
    computer = Computer(Race.Protoss, Difficulty_VeryHard)
    # computer = Computer(Race.Random, Difficulty_Hard)

    sc2.run_game(
        sc2.maps.get("YearZeroLE"),
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), Computer(enemy_race, Difficulty.VeryHard)], realtime=False,
    )



if __name__ == "__main__":
    main()
