import sys, os
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

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

    def on_upgrade_complete(self, upgrade: UpgradeId):
        if upgrade == BuffId.RESONATINGGLAIVESPHASESHIFT:
            print("UPGRADE COMPLETE")
            self.resonating_glaves = True
    def __init__(self):
        super().__init__()
        self.save_minerals = False
        self.save_vespene = False

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
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return
        else:
            nexus = self.townhalls.random

        # order these by priority

        self.make_probes(nexus)

        self.build_pylons(nexus)

        self.build_gateways()

        self.do_upgrades()

        self.make_army()

        # # If we have no forge, build one near the pylon that is closest to our starting nexus
        # elif not self.structures(UnitTypeId.FORGE):
        #     pylon_ready = self.structures(UnitTypeId.PYLON).ready
        #     if pylon_ready:
        #         if self.can_afford(UnitTypeId.FORGE):
        #             await self.build(UnitTypeId.FORGE, near=pylon_ready.closest_to(nexus))
        #
        # # If we have less than 2 pylons, build one at the enemy base
        # elif self.structures(UnitTypeId.PYLON).amount < 2:
        #     if self.can_afford(UnitTypeId.PYLON):
        #         pos = self.enemy_start_locations[0].towards(self.game_info.map_center, random.randrange(8, 15))
        #         await self.build(UnitTypeId.PYLON, near=pos)
        #
        # # If we have no cannons but at least 2 completed pylons, automatically find a placement location and build them near enemy start location
        # elif not self.structures(UnitTypeId.PHOTONCANNON):
        #     if self.structures(UnitTypeId.PYLON).ready.amount >= 2 and self.can_afford(UnitTypeId.PHOTONCANNON):
        #         pylon = self.structures(UnitTypeId.PYLON).closer_than(20, self.enemy_start_locations[0]).random
        #         await self.build(UnitTypeId.PHOTONCANNON, near=pylon)
        #
        # # Decide if we should make pylon or cannons, then build them at random location near enemy spawn
        # elif self.can_afford(UnitTypeId.PYLON) and self.can_afford(UnitTypeId.PHOTONCANNON):
        #     # Ensure "fair" decision
        #     for _ in range(20):
        #         pos = self.enemy_start_locations[0].random_on_distance(random.randrange(5, 12))
        #         building = UnitTypeId.PHOTONCANNON if self.state.psionic_matrix.covers(pos) else UnitTypeId.PYLON
        #         await self.build(building, near=pos)

    def make_probes(self, nexus):
        # Make probes until we have 16 total
        if self.supply_workers < 16 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)
            else:
                self.save_for(UnitTypeId.PROBE)

    def build_pylons(self, nexus):
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
        await self.build(UnitTypeId.PYLON, near=nexus)

    def build_gateways(self):
        pass

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
