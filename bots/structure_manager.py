import sc2
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import UnitTypeId, UnitOrder

class StructureManager:

    def __init__(self, ai):
        from bots.resonator_bot import ResonatorBot
        self.ai: ResonatorBot = ai

    async def build_pylon(self, check_supply=True):
        """
        todo: also build
        """
        SUPPLY_BUFFER = 10

        if self.ai.already_pending(UnitTypeId.PYLON) > 0:
            # we are already building a pylon
            return

        if check_supply and self.ai.supply_left > SUPPLY_BUFFER:
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

    async def build_structure(self, unit_id, nexus, cap=1, save=False):
        if self.amount_with_pending(unit_id) >= cap:
            return False

        pylon = self.ai.structures(UnitTypeId.PYLON).ready
        if not pylon:
            return False

        if self.ai.can_afford(unit_id):
            # we should build the structure

            # if self.ai.is_build_ordered():
            #     # a probe is already processing a build order
            #     return False

            result = await self.ai.build(unit_id, near=pylon.closest_to(nexus), max_distance=30)
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

    async def build_gateways(self, nexus, cap, save=False):
        if self.ai.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 1:
            await self.build_structure(UnitTypeId.WARPGATE, nexus, cap=cap, save=save)
        else:
            await self.build_structure(UnitTypeId.GATEWAY, nexus, cap=cap, save=save)

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
