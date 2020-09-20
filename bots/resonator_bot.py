import os
import sys
from math import sqrt
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sc2
from sc2 import Race, Difficulty
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import UnitOrder
from sc2.units import Units, Unit

building_id_list = [UnitTypeId.PYLON, UnitTypeId.GATEWAY, UnitTypeId.STARGATE, UnitTypeId.ROBOTICSFACILITY,
                    UnitTypeId.ROBOTICSBAY, UnitTypeId.ASSIMILATOR]


class ResonatorBot(sc2.BotAI):

    def closest_enemy_combat_unit(self, unitv):
        if self.non_worker_enemies:
            return self.non_worker_enemies.closest_to(unitv.position)
        else:
            return False
    """
    todo:
        research warp gate
        use tech_requirement_progress method
        do something else with chronoboost after glaives are done
        build different unit types
        search code for more todos

        add build order logic
            eg: cybercore: gateway, 200m, 15 probes
    """

    def __init__(self):
        super().__init__()

        self.PROBES_PER_BASE = 16 + 6

        self.save_minerals = False
        self.save_vespene = False

        self.resonating_glaives_started = False

        self.distance_to_enemy_base = 100
        self.wave_amount = 6
        self.sent_adept_wave = False
        self.bulding_for_rally = None
        self.non_worker_enemies: ['Units'] = None

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        if upgrade == BuffId.RESONATINGGLAIVESPHASESHIFT:
            print("resonating glaives complete")

    async def on_building_construction_complete(self, unit):
        print("{} complete @ {}".format(unit, self.time_formatted))
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
        called every fram (~24 fps)
        """
        self.bulding_for_rally = self.structures[0]
        self.save_minerals = False
        self.save_vespene = False
        self.non_worker_enemies = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *building_id_list])

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

        await self.build_pylon(nexus)

        await self.build_gateways(nexus, 1, save=True)

        self.build_assimilators(nexus, 1)
        self.make_probes(nexus, 16 + 3)

        self.build_assimilators(nexus, 2)
        self.make_probes(nexus, 16 + 6)

        await self.expand()

        if self.structures(UnitTypeId.GATEWAY).ready:
            await self.build_structure(UnitTypeId.CYBERNETICSCORE, nexus)
            await self.build_gateways(nexus, 2)

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            self.make_army()
            await self.build_structure(UnitTypeId.TWILIGHTCOUNCIL, nexus)
            await self.build_gateways(nexus, 4)

        if self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount > 0:
            self.build_assimilators(nexus, 2)
            self.make_probes(nexus, 16 + 3 + 3)

        self.do_chronoboost(nexus)

        self.do_upgrades()

        self.do_attack()

        await self.distribute_workers()

        self.check_duplicate_structures()

    def make_probes(self, nexus, cap):
        # Make probes until we have enough
        if self.supply_workers < cap and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)
            else:
                self.save_for(UnitTypeId.PROBE)

    async def build_pylon(self, nexus, check_supply=True):
        """
        todo: also build
        """
        SUPPLY_BUFFER = 5

        if self.already_pending(UnitTypeId.PYLON) > 0:
            # we are already building a pylon
            return

        if check_supply and self.supply_left > SUPPLY_BUFFER:
            # we don't need a pylon
            return

        if not self.can_afford(UnitTypeId.PYLON):
            # can't afford yet
            self.save_for(UnitTypeId.PYLON)
            return

        # find a spot to build it
        map_center = self.game_info.map_center
        position_towards_map_center = self.start_location.towards(map_center, distance=10)
        placement_position = await self.find_placement(
            UnitTypeId.PYLON,
            near=position_towards_map_center,
            placement_step=7
        )
        if not placement_position:
            # placement_position can be None
            return

        # build a pylon
        result = await self.build(UnitTypeId.PYLON, near=placement_position)
        if result:
            print("started pylon @ {} supply={}/{}".format(
                self.time_formatted, self.supply_used, self.supply_cap))

    def build_assimilators(self, nexus, cap=-1):
        """
        Build gas near completed nexus
        """
        if cap > 0:
            if self.amount_with_pending(UnitTypeId.ASSIMILATOR) >= cap:
                return  # we have enough

        vgs = self.vespene_geyser.closer_than(15, nexus)
        for vg in vgs:
            if self.gas_buildings.closer_than(1, vg):
                # there is already a building
                return

            if not self.can_afford(UnitTypeId.ASSIMILATOR):
                self.save_for(UnitTypeId.ASSIMILATOR)
                return

            worker = self.select_build_worker(vg.position)
            if worker is None:
                # worker not available
                return

            # else build
            worker.build(UnitTypeId.ASSIMILATOR, vg)
            worker.stop(queue=True)

    async def build_structure(self, unit_id, nexus, cap=1, save=False):
        if self.amount_with_pending(unit_id) < cap:
            pylon = self.structures(UnitTypeId.PYLON).ready
            if pylon:
                if self.can_afford(unit_id):
                    # we should build the structure

                    # if self.is_build_ordered():
                    #     # a probe is already processing a build order
                    #     return False

                    result = await self.build(unit_id, near=pylon.closest_to(nexus), max_distance=30)
                    print("started building {} @ {} (result={})".format(unit_id, self.time_formatted, result))
                    if not result:
                        # failed to find build location
                        print("building pylon since we couldn't find build location")
                        await self.build_pylon(nexus, check_supply=False)
                    return result
                elif save:
                    self.save_for(unit_id)
        return False

    def is_build_ordered(self):
        """
        sometimes 2 building get queued at the same time
        this is to prevent that from happening

        return True if there is currently a worker with a build order
        """
        workers_not_collecting = [w for w in self.workers if not w.is_collecting]
        for w in workers_not_collecting:
            for order in w.orders:  # type: UnitOrder
                order_name = order.ability.friendly_name
                if 'Build' in order_name:
                    print('already ordered: {}'.format(order_name))
                    return True
        return False

    async def build_gateways(self, nexus, cap, save=False):
        await self.build_structure(UnitTypeId.GATEWAY, nexus, cap=cap, save=save)


    def check_duplicate_structures(self):
        to_check = [
            UnitTypeId.TWILIGHTCOUNCIL,
            UnitTypeId.CYBERNETICSCORE,
        ]
        for unit_id in to_check:
            amount = self.structures(unit_id).amount
            if amount > 1:
                print("duplicate structures detected: {}".format([unit_id, amount]))

    def amount_with_pending(self, unit_id):
        return self.structures(unit_id).ready.amount + self.already_pending(unit_id)

    async def expand(self):
        """
        steps:
            choose base location
            send a probe to build a nexus
            then start building more probes

        todo:
            when to start expanding?
        """
        if not self.sent_adept_wave:
            return

        if self.amount_with_pending(UnitTypeId.NEXUS) < 2:
            if self.can_afford(UnitTypeId.NEXUS):
                msg = "EXPANDING!"
                print(msg)
                # await self.chat_send(msg)
                await self.expand_now()
            else:
                # print("saving to expand")
                self.save_for(UnitTypeId.NEXUS)

        if self.townhalls.ready.amount >= 2:
            nexus = self.townhalls.random
            self.build_assimilators(nexus)
            self.make_probes(nexus, self.PROBES_PER_BASE * 2)

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

    def do_upgrades(self):
        # Research resonating glaives
        if self.resonating_glaives_started:
            return  # already started the research
        if not self.can_afford(UpgradeId.ADEPTPIERCINGATTACK):
            return
        if not self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
            return

        tc = self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
        self.resonating_glaives_started = True
        tc.research(UpgradeId.ADEPTPIERCINGATTACK)

    def make_army(self):
        if not self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            return
        if self.can_afford(UnitTypeId.ADEPT):
            self.train(UnitTypeId.ADEPT)




    def do_attack(self):
        adepts = self.units(UnitTypeId.ADEPT)

        self.distance_to_enemy_base = (
                    abs(self.start_location.position[0] - self.enemy_start_locations[0].position[0]) + (
                        self.start_location.position[1] - self.enemy_start_locations[0].position[1]))

        number_of_adepts_at_base = self.units(UnitTypeId.ADEPT).further_than(self.distance_to_enemy_base / 2,
                                                                             self.enemy_start_locations[0].position)

        number_of_adepts_away = self.units(UnitTypeId.ADEPT).closer_than(self.distance_to_enemy_base / 2,
                                                                         self.enemy_start_locations[0].position)

        enemy_combat_units = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *building_id_list])
        enemy_expansions = self.enemy_structures(UnitTypeId.NEXUS)

        probes = self.enemy_units(UnitTypeId.PROBE)
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
                    if enemy_combat_units.closer_than(unit.ground_range + 6.0,
                                          unit) or unit.in_ability_cast_range(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, enemy_mineral_field.position):

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
                        unit.attack(adepts.closest_to(unit).position)

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
                    phase_shift.move(probes.furthest_to(closest_enemy))
                else:
                    if enemy_expansions:
                        phase_shift.move(enemy_expansions.furthest_to(closest_enemy.position))
                    else:
                        phase_shift.move(enemy_mineral_field.position)

                if len(self.enemy_units.closer_than(closest_enemy.ground_range, phase_shift.position)) > len(self.units.closer_than(5, phase_shift.position)) and phase_shift.buff_duration_remain < 5:
                    phase_shift(AbilityId.CANCEL_ADEPTSHADEPHASESHIFT)


            else:
                if probes:
                    phase_shift.move(probes.closest_to(phase_shift.position))
                else:
                    phase_shift.move(enemy_expansions.closest_to(phase_shift.position))


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
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), Computer(Race.Protoss, Difficulty.VeryHard)], realtime=False,
    )



if __name__ == "__main__":
    main()
