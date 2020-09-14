import sys, os
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from random import randint

import sc2
from sc2 import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.player import Bot, Computer
from bots.wave import Wave

class ResonatorBot(sc2.BotAI):

    resonating_glaves_started = False
    waves: ['Wave'] = []
    start_enemy_minerals = None

    def __init__(self):
        super().__init__()
        self.save_minerals = False
        self.save_vespene = False

        self.distance_to_enemy_base = 100
        self.wave_amount = 6

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        if upgrade == BuffId.RESONATINGGLAIVESPHASESHIFT:
            print("resonating glaves complete")

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
        self.save_minerals = False
        self.save_vespene = False

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

        await self.distribute_workers()

        # order these by priority

        self.make_probes(nexus)

        await self.build_pylons(nexus)

        await self.build_gateways(nexus, 1, save=True)

        self.build_assimilators(nexus)

        await self.build_structure(UnitTypeId.CYBERNETICSCORE, nexus)

        await self.build_gateways(nexus, 2)

        await self.build_structure(UnitTypeId.TWILIGHTCOUNCIL, nexus)

        await self.build_gateways(nexus, 4)

        self.do_chronoboost(nexus)

        self.do_upgrades()

        self.make_army()

        self.do_attack()

    def make_probes(self, nexus):
        # Make probes until we have enough
        if self.supply_workers < 22 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)
            else:
                self.save_for(UnitTypeId.PROBE)

    async def build_pylons(self, nexus):
        SUPPLY_BUFFER = 10

        if self.already_pending(UnitTypeId.PYLON) > 0:
            # we are already building a pylon
            return

        if self.supply_left > SUPPLY_BUFFER:
            # we don't need a pylon
            return

        if not self.can_afford(UnitTypeId.PYLON):
            # can't afford yet
            self.save_for(UnitTypeId.PYLON)
            return

        # build a pylon
        return await self.build(UnitTypeId.PYLON, near=nexus)

    def build_assimilators(self, nexus):
        """
        Build gas near completed nexus
        """
        vgs = self.vespene_geyser.closer_than(15, nexus)
        for vg in vgs:
            if self.gas_buildings.closer_than(1, vg):
                # there is already a building
                # todo: assign workers
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

    async def build_structure(self, id, nexus, cap=1, save=False):
        if self.structures(id).amount < cap:
            pylon = self.structures(UnitTypeId.PYLON).ready
            if pylon:
                if self.can_afford(id):
                    await self.build(id, near=pylon.closest_to(nexus))
                elif save:
                    self.save_for(id)

            # todo: add logic to build pylon if needed

    async def build_gateways(self, nexus, cap, save=False):
        await self.build_structure(UnitTypeId.GATEWAY, nexus, cap=cap, save=save)

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
        # Research resonating glaves
        if self.resonating_glaves_started:
            return  # already started the research
        if not self.can_afford(UpgradeId.ADEPTPIERCINGATTACK):
            return
        if not self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
            return

        tc = self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
        # print("AbilityId.RESEARCH_ADEPTRESONATINGGLAIVES: {}".format(self.calculate_cost(AbilityId.RESEARCH_ADEPTRESONATINGGLAIVES)))
        # print("UpgradeId.ADEPTPIERCINGATTACK: {}".format(self.calculate_cost(UpgradeId.ADEPTPIERCINGATTACK)))
        self.resonating_glaves_started = True
        tc.research(UpgradeId.ADEPTPIERCINGATTACK)

    def make_army(self):
        if not self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            return
        if self.can_afford(UnitTypeId.ADEPT):
            self.train(UnitTypeId.ADEPT)

    def do_attack(self):
        adepts = self.units(UnitTypeId.ADEPT)

        self.distance_to_enemy_base = (abs(self.start_location.position[0] - self.enemy_start_locations[0].position[0]) + (self.start_location.position[1] - self.enemy_start_locations[0].position[1]))

        number_of_adepts_at_base = self.units(UnitTypeId.ADEPT).further_than(self.distance_to_enemy_base/2, self.enemy_start_locations[0].position)

        number_of_adepts_away = self.units(UnitTypeId.ADEPT).closer_than(self.distance_to_enemy_base/2, self.enemy_start_locations[0].position)

        probes = self.enemy_units(UnitTypeId.PROBE)
        enemy_mineral_field = self.mineral_field.closest_to(self.enemy_start_locations[0])
        if number_of_adepts_at_base.amount >= self.wave_amount:
            for unit in adepts:
                unit.attack(self.enemy_start_locations[0])
        for unit in number_of_adepts_away:
            if probes:
                unit.attack(probes.random)
                unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, probes.random.position)
            else:
                non_worker_enemies = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV])
                if non_worker_enemies:
                    closest_non_worker_enemy = non_worker_enemies.closest_to(unit.position)
                    if adepts.closer_than(unit.ground_range + 4.0, closest_non_worker_enemy):
                        unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, enemy_mineral_field.position)
                else:
                    enemy_buildings = self.enemy_structures
                    if enemy_buildings:
                        closest_building = enemy_buildings.closest_to(unit.position)
                        unit.attack(closest_building)

        phase_shifts = self.units(UnitTypeId.ADEPTPHASESHIFT)
        for phase_shift in phase_shifts:
            if probes:
                phase_shift.move(probes.closest_to(phase_shift.position))
            else:
                phase_shift.move(enemy_mineral_field.position)






def main():
    sc2.run_game(
        sc2.maps.get("YearZeroLE"),
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
