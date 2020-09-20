import sc2
from sc2.unit import UnitTypeId

class StructureManager:

    def __init__(self, ai):
        from bots.resonator_bot import ResonatorBot
        self.ai: ResonatorBot = ai

    async def build_pylon(self, nexus, check_supply=True):
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