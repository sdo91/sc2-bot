from collections import defaultdict
from typing import List

from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import UnitTypeId, UnitOrder


class StructureManager:

    def __init__(self, ai):
        from bots.resonator_bot import ResonatorBot
        self.ai: ResonatorBot = ai

        self.enemy_check_time = 0
        self.is_rush_detected = False

    def choose_new_pylon_nexus(self) -> Point2:
        """
        Returns:
            position of nexus w/ fewest pylons
        """
        counts = defaultdict(int)
        for nexus in self.ai.structures(UnitTypeId.NEXUS):
            counts[nexus.position] = 0
        for pylon in self.ai.structures(UnitTypeId.PYLON):
            nexus = self.ai.structures(UnitTypeId.NEXUS).closest_to(pylon)
            counts[nexus.position] += 1
        # print('PYLON COUNTS: {}'.format(counts))

        min_count = 99
        result = self.ai.townhalls.random.position
        for nexus_pos in counts:
            count_at_nexus = counts[nexus_pos]
            if count_at_nexus < min_count:
                min_count = count_at_nexus
                result = nexus_pos
        # print('min_nexus: {}'.format(min_nexus))
        return result

    async def build_pylon(self, check_supply=True):
        """
        todo:
            improve placement
            build at other bases
        """
        num_gates = self.ai.structures(self.get_gate_id()).ready.amount
        if num_gates >= 2:
            supply_buffer = 10
        else:
            supply_buffer = 2

        if self.ai.already_pending(UnitTypeId.PYLON) > 0:
            # we are already building a pylon
            return

        if self.ai.supply_cap == 200:
            # at max supply
            return

        if check_supply and self.ai.supply_left > supply_buffer:
            # we don't need a pylon
            return

        if not self.ai.can_afford(UnitTypeId.PYLON):
            # can't afford yet
            self.ai.save_for(UnitTypeId.PYLON)
            return

        # choose a nexus
        nexus_position = self.choose_new_pylon_nexus()

        # find a spot to build it
        map_center = self.ai.game_info.map_center
        position_towards_map_center = nexus_position.towards(map_center, distance=10)
        placement_position = await self.ai.find_placement(
            UnitTypeId.PYLON,
            near=position_towards_map_center,
            placement_step=7
        )
        if not placement_position:
            # placement_position can be None
            return

        # build a pylon
        result = await self.ai.build(UnitTypeId.PYLON, near=placement_position)
        if result:
            print("started pylon @ {} supply={}/{}".format(
                self.ai.time_formatted, self.ai.supply_used, self.ai.supply_cap))

    def build_assimilators(self, nexus, cap=-1):
        """
        Build gas near completed nexus
        """
        if cap > 0:
            if self.amount_with_pending(UnitTypeId.ASSIMILATOR) >= cap:
                return  # we have enough

        vgs = self.ai.vespene_geyser.closer_than(15, nexus)
        for vg in vgs:
            if self.ai.gas_buildings.closer_than(1, vg):
                # there is already a building
                return

            if not self.ai.can_afford(UnitTypeId.ASSIMILATOR):
                self.ai.save_for(UnitTypeId.ASSIMILATOR)
                return

            worker = self.ai.select_build_worker(vg.position)
            if worker is None:
                # worker not available
                return

            # else build
            worker.build(UnitTypeId.ASSIMILATOR, vg)
            worker.stop(queue=True)
            return

    async def build_structure(self, unit_id, cap=1, save=True):
        """
        Returns:
            bool: True if the build was started
        """
        if 0 < cap <= self.amount_with_pending(unit_id):
            return False

        if self.ai.tech_requirement_progress(unit_id) < 1:
            return  # can't make yet

        ready_pylons = self.ai.structures(UnitTypeId.PYLON).ready
        if not ready_pylons:
            return False

        if self.ai.can_afford(unit_id):
            # we should build the structure
            num_tries = 5
            success = False
            for _ in range(num_tries):
                pylon = ready_pylons.random
                success = await self.ai.build(unit_id, near=pylon, max_distance=30)
                print("started building {} @ {} (success={})".format(unit_id, self.ai.time_formatted, success))
                if success:
                    break
                else:
                    print("try again to find build location")
            if not success:
                # failed to find build location
                print("building pylon since we couldn't find build location")
                await self.ai.structure_manager.build_pylon(check_supply=False)
            return success
        elif save:
            self.ai.save_for(unit_id)

        return False

    def is_build_ordered(self):
        """
        sometimes 2 building get queued at the same time
        this is to prevent that from happening

        return True if there is currently a worker with a build order
        """
        workers_not_collecting = [w for w in self.ai.workers if not w.is_collecting]
        for w in workers_not_collecting:
            for order in w.orders:  # type: UnitOrder
                order_name = order.ability.friendly_name
                if 'Build' in order_name:
                    print('already ordered: {}'.format(order_name))
                    return True
        return False

    def get_gate_id(self):
        if self.ai.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) < 1:
            return UnitTypeId.GATEWAY
        else:
            return UnitTypeId.WARPGATE

    async def build_gateways(self, nexus, cap, save=False):
        gate_id = self.get_gate_id()
        await self.build_structure(gate_id, cap=cap, save=save)

    def check_duplicate_structures(self):
        to_check = [
            UnitTypeId.TWILIGHTCOUNCIL,
            UnitTypeId.CYBERNETICSCORE,
        ]
        for unit_id in to_check:
            amount = self.ai.structures(unit_id).amount
            if amount > 1:
                print("duplicate structures detected: {}".format([unit_id, amount]))

    def amount_with_pending(self, unit_id):
        return self.ai.structures(unit_id).ready.amount + self.ai.already_pending(unit_id)

    async def do_expand_check(self):
        await self.expand(2)
        if self.ai.time > 60 * 8:
            await self.expand(3)
        if self.ai.time > 60 * 12:
            await self.expand(4)
        if self.ai.time > 60 * 16:
            await self.expand(5)
        if self.ai.time > 60 * 20:
            await self.expand(6)
        if self.ai.time > 60 * 24:
            await self.expand(7)

    async def expand(self, cap: int):
        """
        steps:
            choose base location
            send a probe to build a nexus
            then start building more probes
        """
        if self.amount_with_pending(UnitTypeId.NEXUS) < cap:
            if self.ai.can_afford(UnitTypeId.NEXUS):
                msg = "EXPANDING!"
                print(msg)
                # await self.ai.chat_send(msg)
                await self.ai.expand_now()
            else:
                # print("saving to expand")
                self.ai.save_for(UnitTypeId.NEXUS)

        # todo: improve this logic
        if self.ai.townhalls.ready.amount >= cap:
            nexus = self.ai.townhalls.random
            self.build_assimilators(nexus)
            self.ai.make_probes(nexus, self.ai.PROBES_PER_BASE * cap)

    async def build_extras(self):
        if self.ai.minerals > 2000:
            return

        await self.build_structure(UnitTypeId.STARGATE, 2, save=False)
        gate_id = self.get_gate_id()
        await self.build_structure(gate_id, cap=6, save=False)

    async def get_enemy_base_locations(self) -> List[Point2]:
        """
        returns a list of enemy base locations, ordered by closet to enemy start
        """
        start = self.ai.enemy_start_locations[0]

        # create map of locations by dist
        locations_by_dist = {}
        for location in self.ai.expansion_locations_list:
            distance = await self.ai._client.query_pathing(start, location)
            if distance is None:
                continue
            locations_by_dist[distance] = location

        # sort and return
        sorted_distances = sorted(locations_by_dist.keys())
        result = [start]  # we also want the enemy start location
        for d in sorted_distances:
            result.append(locations_by_dist[d])
        return result

    @classmethod
    def count_units(cls, units):
        counts = defaultdict(int)
        for u in units:
            counts[u.name] += 1
        return counts

    async def check_for_rush(self):
        if self.is_rush_detected or self.ai.time > 2.25*60:
            return
        num_bases = self.ai.enemy_structures.of_type(self.ai.expansion_types).amount
        if self.ai.time > 2*60 and num_bases == 1:
            # enemy should have 2nd base by now, potential rush
            await self.ai.chat_send("potential rush detected")
            self.is_rush_detected = True

    async def check_enemy_buildings(self):
        now = self.ai.time
        elapsed = now - self.enemy_check_time
        if elapsed > 10:
            self.enemy_check_time = now

            print('structures @ {}: {}'.format(
                self.ai.time_formatted, self.count_units(self.ai.enemy_structures)))
            await self.check_for_rush()

            print('units @ {}: {}'.format(
                self.ai.time_formatted, self.count_units(self.ai.enemy_units)))
