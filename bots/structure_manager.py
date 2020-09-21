import sc2
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import UnitTypeId, UnitOrder

class StructureManager:

    def __init__(self, ai):
        from bots.resonator_bot import ResonatorBot
        self.ai: ResonatorBot = ai

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

        # find a spot to build it
        map_center = self.ai.game_info.map_center
        position_towards_map_center = self.ai.start_location.towards(map_center, distance=10)
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
        if 0 < cap <= self.amount_with_pending(unit_id):
            return False

        if self.ai.tech_requirement_progress(unit_id) < 1:
            return  # can't make yet

        ready_pylons = self.ai.structures(UnitTypeId.PYLON).ready
        if not ready_pylons:
            return False
        pylon = ready_pylons.random

        if self.ai.can_afford(unit_id):
            # we should build the structure

            # if self.ai.is_build_ordered():
            #     # a probe is already processing a build order
            #     return False

            result = await self.ai.build(unit_id, near=pylon, max_distance=30)
            print("started building {} @ {} (result={})".format(unit_id, self.ai.time_formatted, result))
            if not result:
                # failed to find build location
                print("building pylon since we couldn't find build location")
                await self.ai.structure_manager.build_pylon(check_supply=False)
            return result
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
