import os
import sys
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sc2
from sc2 import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.unit import UnitOrder
from sc2.player import Bot, Computer


class ResonatorBot(sc2.BotAI):
    """
    todo:
        add pylon build logic
        expand to 2nd base
        research warp gate
        use tech_requirement_progress
        do something else with chronoboost after glaves are done
        build different unit types
    """

    def __init__(self):
        super().__init__()

        self.save_minerals = False
        self.save_vespene = False

        self.resonating_glaves_started = False

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

        # order these by priority

        self.make_probes(nexus)

        await self.build_pylons(nexus)

        await self.build_gateways(nexus, 1, save=True)

        self.build_assimilators(nexus)

        if self.structures(UnitTypeId.GATEWAY).ready:
            await self.build_structure(UnitTypeId.CYBERNETICSCORE, nexus)

        await self.build_gateways(nexus, 2)

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            await self.build_structure(UnitTypeId.TWILIGHTCOUNCIL, nexus)

        await self.build_gateways(nexus, 4)

        self.do_chronoboost(nexus)

        self.do_upgrades()

        self.make_army()

        self.do_attack()

        await self.distribute_workers()

        self.check_duplicate_structures()

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
        # todo: add logic to build pylon if needed
        if self.structures(unit_id).amount < cap:
            pylon = self.structures(UnitTypeId.PYLON).ready
            if pylon:
                if self.can_afford(unit_id):
                    # we should build the structure

                    if self.is_build_ordered():
                        # a probe is already processing a build order
                        return False

                    result = await self.build(unit_id, near=pylon.closest_to(nexus))
                    print("building: {}, {}".format(unit_id, result))
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
        if adepts.amount > 6:
            probes = self.enemy_units(UnitTypeId.PROBE)
            for unit in adepts:
                unit.attack(self.enemy_start_locations[0])
                if probes:
                    unit.attack(probes.random)
                    unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, probes.random.position)
                else:
                    non_worker_enemies = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV])
                    if non_worker_enemies:
                        closest_non_worker_enemy = non_worker_enemies.closest_to(unit.position)
                        if adepts.closer_than(unit.ground_range, closest_non_worker_enemy):
                            unit(AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, self.mineral_field.closest_to(self.enemy_start_locations[0]))





def main():
    # difficulty = Difficulty.Easy
    # difficulty = Difficulty.Medium
    difficulty = Difficulty.Hard

    sc2.run_game(
        sc2.maps.get("YearZeroLE"),
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), Computer(Race.Protoss, difficulty)],
        # realtime=True,
        realtime=False,
    )


if __name__ == "__main__":
    main()
