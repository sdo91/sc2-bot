import sys, os
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import random

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

    resonating_glaves = False
    waves: ['Wave'] = []

    def __init__(self):
        super().__init__()
        self.save_minerals = False
        self.save_vespene = False

    def on_upgrade_complete(self, upgrade: UpgradeId):
        if upgrade == BuffId.RESONATINGGLAIVESPHASESHIFT:
            print("UPGRADE COMPLETE")
            self.resonating_glaves = True

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

        await self.build_gateways(nexus, 1)

        self.build_assimilator(nexus)

        await self.build_structure(UnitTypeId.CYBERNETICSCORE, nexus)

        await self.build_gateways(nexus, 2)

        await self.build_structure(UnitTypeId.TWILIGHTCOUNCIL, nexus)

        await self.build_gateways(nexus, 4)

        self.do_upgrades()

        self.make_army()

    def make_probes(self, nexus):
        # Make probes until we have 16 total
        if self.supply_workers < 16 and nexus.is_idle:
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

    def build_assimilator(self, nexus):
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

    async def build_gateways(self, nexus, cap):
        await self.build_structure(UnitTypeId.GATEWAY, nexus, cap=cap, save=False)

    def do_upgrades(self):
        if not self.resonating_glaves:
            if self.units(UnitTypeId.TWILIGHTCOUNCIL).idle:
                self.can_afford(UpgradeId.ADEPTKILLBOUNCE)
                self.units(UnitTypeId.TWILIGHTCOUNCIL).train(BuffId.RESONATINGGLAIVESPHASESHIFT)
            else:
                for nx in self.units(UnitTypeId.NEXUS):
                    self.can_cast(nx, AbilityId.EFFECT_CHRONOBOOST, self.units(UnitTypeId.TWILIGHTCOUNCIL).first)

    def make_army(self):
        gateways = self.units(UnitTypeId.GATEWAY).idle
        if self.can_afford(UnitTypeId.ADEPT) and gateways:
            for g in gateways:
                g.train(UnitTypeId.ADEPT)

    def do_attack(self):
        new_wave: Wave = None
        for unit in self.units(UnitTypeId.ADEPT):
            if unit.assigned == False:
                if not new_wave:
                    new_wave = Wave()
                    self.waves.append(new_wave)
                    new_wave.append(unit)
                else:
                    new_wave.units.append(unit)



        for wave in self.waves:
            if len(wave.units) < 1:
                self.waves.remove(wave)
                continue
            wave.do()




def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), Computer(Race.Protoss, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
