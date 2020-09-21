from sc2 import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId



DIFFICULTY_EASY = Difficulty.Easy
DIFFICULTY_MEDIUM = Difficulty.Medium
DIFFICULTY_HARD = Difficulty.Hard
DIFFICULTY_VERYHARD = Difficulty.VeryHard

RACE_ZERG = Race.Zerg
RACE_TERRAN = Race.Terran
RACE_PROTOSS = Race.Protoss



ZERG_EXPANSION_IDS = [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE]
TERRAN_EXPANSION_IDS = [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS]
PROTOSS_EXPANSION_IDS = [UnitTypeId.NEXUS]



ZERG_BUILDING_IDS = [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.SPAWNINGPOOL,
                      UnitTypeId.EVOLUTIONCHAMBER, UnitTypeId.SPIRE] + ZERG_EXPANSION_IDS

PROTOSS_BUILDING_IDS = [UnitTypeId.PYLON, UnitTypeId.GATEWAY, UnitTypeId.STARGATE, UnitTypeId.ROBOTICSFACILITY,
                         UnitTypeId.ROBOTICSBAY, UnitTypeId.ASSIMILATOR] + PROTOSS_EXPANSION_IDS

TERRAN_BUILDING_IDS = [UnitTypeId.COMMANDCENTERFLYING,
                        UnitTypeId.ORBITALCOMMANDFLYING, UnitTypeId.BARRACKS,
                        UnitTypeId.BARRACKSFLYING, UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKSTECHLAB,
                        UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING, UnitTypeId.FACTORYREACTOR,
                        UnitTypeId.FACTORYTECHLAB, UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING,
                        UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORTTECHLAB, UnitTypeId.SUPPLYDEPOT,
                        UnitTypeId.ENGINEERINGBAY, UnitTypeId.ARMORY] + TERRAN_EXPANSION_IDS