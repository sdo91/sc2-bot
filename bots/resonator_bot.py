import os
import sys
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bots.structure_manager import StructureManager
from bots.army_manager import ArmyManager
from bots import constants

from random import randint

import sc2
from sc2 import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.player import Bot, Computer, Human
from sc2.units import Units, Unit

# realtime = True
realtime = False

from examples.zerg.zerg_rush import ZergRushBot
from examples.zerg.expand_everywhere import ExpandEverywhere
enemy_ai_list = [Computer(constants.RACE_ZERG, constants.DIFFICULTY_VERYHARD)]
enemy_ai = enemy_ai_list[randint(0, len(enemy_ai_list) - 1)]


enemy_race = constants.RACE_ZERG
enemy_player = enemy_ai
# enemy_player = Human(enemy_race, name="Human")


class ResonatorBot(sc2.BotAI):
    """
    todo:
        fix make probes to make enough to saturate
        expand more
        buy unit upgrades
        build different unit types
        do something else with chronoboost after glaives are done
        search code for more todos
        build photon canons for base defense?
        need to send units to scout with
        need to work on base defense

        add build order logic
            eg: cybercore: gateway, 200m, 15 probes
    """

    building_id_list: ['UnitTypeId'] = None
    expansion_types: ['UnitTypeId'] = None
    enemy_worker_type: UnitTypeId = None
    enemy_anti_air_types: ['UnitTypeId'] = None

    if enemy_race == Race.Zerg:
        building_id_list = constants.ZERG_BUILDING_IDS
        enemy_worker_type = UnitTypeId.DRONE
        expansion_types = constants.ZERG_EXPANSION_IDS
        enemy_anti_air_types = constants.ZERG_ANTI_AIR_STUFF
    elif enemy_race == Race.Terran:
        building_id_list = constants.TERRAN_BUILDING_IDS
        enemy_worker_type = UnitTypeId.SCV
        expansion_types = constants.TERRAN_EXPANSION_IDS
        enemy_anti_air_types = constants.TERRAN_ANTI_AIR_STUFF
    else:
        building_id_list = constants.PROTOSS_BUILDING_IDS
        enemy_worker_type = UnitTypeId.PROBE
        expansion_types = constants.PROTOSS_EXPANSION_IDS
        enemy_anti_air_types = constants.PROTOSS_ANTI_AIR_STUFF

    def closest_enemy_combat_unit(self, unitv):
        if self.non_worker_enemies:
            return self.non_worker_enemies.closest_to(unitv.position)
        else:
            return False

    def __init__(self):
        super().__init__()

        self.structure_manager = StructureManager(self)
        self.army_manager = ArmyManager(self)

        self.PROBES_PER_BASE = 16 + 6
        self.enemy_base_locations = []

        self.scout = None
        self.scout_send_times = [40, 2*60, 3*60, 4*60, 5*60]

        self.save_minerals = False
        self.save_vespene = False

        self.distance_to_enemy_base = 100
        self.wave_amount = 6
        self.bulding_for_rally = None
        self.non_worker_enemies: ['Units'] = None

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        print("{} upgrade complete @ {}".format(upgrade, self.time_formatted))

    async def on_building_construction_complete(self, unit: Unit):
        print("building complete: {} @ {}".format(unit.name, self.time_formatted))
        if unit.type_id == self.structure_manager.get_gate_id():
            unit(AbilityId.RALLY_BUILDING, self.start_location.towards(self.game_info.map_center, 15))

    async def on_unit_created(self, unit: Unit):
        if unit.type_id == UnitTypeId.PROBE and 13 <= self.supply_workers <= 22:
            print("worker count: {}".format(self.supply_workers))

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

    async def on_start(self):
        self.enemy_base_locations = await self.structure_manager.get_enemy_base_locations()

    async def on_step(self, iteration):
        """
        called every frame (~24 fps)
        """
        self.bulding_for_rally = self.structures[0]
        self.save_minerals = False
        self.save_vespene = False
        self.non_worker_enemies = self.enemy_units.exclude_type(
            [UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *self.building_id_list, UnitTypeId.OVERLORD,
             UnitTypeId.MEDIVAC])

        # if iteration == 0:
        #     await self.chat_send("todo: add trash talk here")

        if not self.townhalls:
            # todo: improve this logic
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return
        else:
            nexus = self.townhalls.random

        await self.scout_enemy()
        self.structure_manager.check_enemy_buildings()

        await self.do_build_order(nexus)

        self.do_chronoboost(nexus)

        self.army_manager.do_attack()

        await self.distribute_workers()

        self.structure_manager.check_duplicate_structures()

    async def scout_enemy(self):
        if not self.scout_send_times:
            # dont need to send any more
            return
        if self.time < self.scout_send_times[0]:
            # not time to send yet
            return

        print("sending scout @ {}".format(self.time_formatted))
        self.scout_send_times.pop(0)

        # send the scout
        self.scout = self.workers.random
        for x in range(6):
            queue = (x > 0)
            self.scout.move(self.enemy_base_locations[x % 3], queue=queue)

    async def do_build_order(self, nexus):
        """
        NOTE: Ordered these by priority

        build order from here: https://liquipedia.net/starcraft2/2_Gate_Adept_Harass
        13/14 Pylon
        15/16 Gateway
        17 Assimilator
        18 Gateway
        19 @100% Gateway, start Cybernetics Core
        20 Pylon
        22 Assimilator
        22 @100% Cybernetics Core, start two Adepts and Warpgate Research
        """
        if self.probes_less_than(nexus, 14):
            return
        await self.structure_manager.build_pylon()

        if self.probes_less_than(nexus, 15):
            return
        await self.structure_manager.build_gateways(nexus, 1, save=True)

        if self.probes_less_than(nexus, 17):
            return
        self.structure_manager.build_assimilators(nexus, 1)

        if self.probes_less_than(nexus, 18):
            return
        await self.structure_manager.build_gateways(nexus, 2, save=True)

        # build as soon as 1st gateway is done
        await self.structure_manager.build_structure(UnitTypeId.CYBERNETICSCORE)

        if self.probes_less_than(nexus, 22):
            return
        self.structure_manager.build_assimilators(nexus, 2)

        self.do_research(UnitTypeId.TWILIGHTCOUNCIL, UpgradeId.ADEPTPIERCINGATTACK)

        if self.army_manager.sent_adept_wave:
            await self.structure_manager.build_structure(UnitTypeId.STARGATE)
            await self.structure_manager.expand(2)
            if self.time > 60 * 8:
                await self.structure_manager.expand(3)
            if self.time > 60 * 12:
                await self.structure_manager.expand(4)

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            self.make_army()
            await self.structure_manager.build_structure(UnitTypeId.TWILIGHTCOUNCIL)
            self.do_research(UnitTypeId.CYBERNETICSCORE, UpgradeId.WARPGATERESEARCH)

        if self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount > 0:
            await self.structure_manager.build_gateways(nexus, 4)

        # await self.structure_manager.build_extras()

    def probes_less_than(self, nexus, num):
        if self.supply_workers < num:
            # we should wait
            self.make_probes(nexus, num)
            return True
        else:
            return False

    def make_probes(self, nexus, cap):
        # Make probes until we have enough
        if self.supply_workers < cap and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)
            else:
                self.save_for(UnitTypeId.PROBE)

    def do_chronoboost(self, nexus: Unit):
        if nexus.energy < 50:
            return  # not enough

        if self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
            tc = self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
            if not tc.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not tc.is_idle:
                # todo: make sure this is working
                result = nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, tc)
                # print("boosting twilight council @ {}, {}".format(self.time_formatted, result))
                return
        else:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not nexus.is_idle:
                print("boosting nexus")
                nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)

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

    def have_enough_phoenix(self):
        try:
            if (len(self.units(UnitTypeId.ORACLE)) / (1 + len(self.units(UnitTypeId.PHOENIX)))) > 3:
                return False
            return True
        except ZeroDivisionError:
            return True

    def make_army(self):
        if self.army_manager.sent_adept_wave:
            if self.structures(UnitTypeId.STARGATE).idle:
                # if we have an idle stargate, build oracle ASAP
                if not self.have_enough_phoenix():
                    self.make_unit(UnitTypeId.PHOENIX, save=True)

                self.make_unit(UnitTypeId.ORACLE, save=True)
        self.make_unit(UnitTypeId.ADEPT)

    def make_unit(self, unit_id, save=False):
        if self.tech_requirement_progress(unit_id) < 1:
            return
        if self.can_afford(unit_id):
            self.train(unit_id, train_only_idle_buildings=True)
        elif save:
            self.save_for(unit_id)


def main():
    sc2.run_game(
        sc2.maps.get("YearZeroLE"),
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), enemy_player],
        realtime=realtime,
    )


if __name__ == "__main__":
    main()
