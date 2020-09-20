import os
import sys
from typing import Union

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bots.structure_manager import StructureManager
from bots.army_manager import ArmyManager
import bots.constants as constants


import sc2
from sc2 import Race, Difficulty
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.player import Bot, Computer
from sc2.units import Units, Unit

enemy_race = Race.Protoss


class ResonatorBot(sc2.BotAI):
    """
    todo:
        expand more
        build different unit types
        do something else with chronoboost after glaives are done
        search code for more todos

        add build order logic
            eg: cybercore: gateway, 200m, 15 probes
    """

    building_id_list: ['UnitTypeId'] = None
    expansion_types: ['UnitTypeId'] = None
    enemy_worker_type: UnitTypeId = None

    if enemy_race == Race.Zerg:
        building_id_list = constants.ZERG_BUILDING_IDS
        enemy_worker_type = UnitTypeId.DRONE
        expansion_types = constants.ZERG_EXPANSION_IDS
    elif enemy_race == Race.Terran:
        building_id_list = constants.TERRAN_BUILDING_IDS
        enemy_worker_type = UnitTypeId.SCV
        expansion_types = constants.TERRAN_EXPANSION_IDS
    else:
        building_id_list = constants.PROTOSS_BUILDING_IDS
        enemy_worker_type = UnitTypeId.PROBE
        expansion_types = constants.PROTOSS_EXPANSION_IDS

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
        self.non_worker_enemies = self.enemy_units.exclude_type([UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, *self.building_id_list, UnitTypeId.OVERLORD, UnitTypeId.MEDIVAC])

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

        self.do_research(UnitTypeId.TWILIGHTCOUNCIL, UpgradeId.ADEPTPIERCINGATTACK)

        self.structure_manager.build_assimilators(nexus, 2)
        self.make_probes(nexus, 16 + 6)

        if self.sent_adept_wave:
            await self.structure_manager.expand(2)
        if self.time > 60 * 6:
            await self.structure_manager.expand(3)

        if self.structures(UnitTypeId.GATEWAY).ready:
            await self.structure_manager.build_structure(UnitTypeId.CYBERNETICSCORE, nexus)
            await self.structure_manager.build_gateways(nexus, 2)

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            await self.structure_manager.build_structure(UnitTypeId.STARGATE, nexus)
            await self.structure_manager.build_structure(UnitTypeId.TWILIGHTCOUNCIL, nexus)
            self.do_research(UnitTypeId.CYBERNETICSCORE, UpgradeId.WARPGATERESEARCH)
            self.make_army()
            await self.structure_manager.build_gateways(nexus, 4)

        if self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount > 0:
            self.structure_manager.build_assimilators(nexus, 2)
            self.make_probes(nexus, 16 + 3 + 3)

        self.do_chronoboost(nexus)

        self.army_manager.do_attack()

        await self.distribute_workers()

        self.structure_manager.check_duplicate_structures()

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

    def make_army(self):
        if self.structures(UnitTypeId.STARGATE).idle:
            # if we have an idle stargate, build oracle ASAP
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
        [Bot(Race.Protoss, ResonatorBot(), name="ResonatorBot"), Computer(enemy_race, Difficulty.VeryHard)],
        # realtime=True,
        realtime=False,
    )



if __name__ == "__main__":
    main()
