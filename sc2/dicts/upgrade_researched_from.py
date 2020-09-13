# THIS FILE WAS AUTOMATICALLY GENERATED BY "generate_dicts_from_data_json.py" DO NOT CHANGE MANUALLY!
# ANY CHANGE WILL BE OVERWRITTEN

from ..ids.unit_typeid import UnitTypeId
from ..ids.ability_id import AbilityId
from ..ids.upgrade_id import UpgradeId

# from ..ids.buff_id import BuffId
# from ..ids.effect_id import EffectId

from typing import Dict, Set, Union

UPGRADE_RESEARCHED_FROM: Dict[UpgradeId, UnitTypeId] = {
    UpgradeId.ADEPTPIERCINGATTACK: UnitTypeId.TWILIGHTCOUNCIL,
    UpgradeId.ANABOLICSYNTHESIS: UnitTypeId.ULTRALISKCAVERN,
    UpgradeId.BANSHEECLOAK: UnitTypeId.STARPORTTECHLAB,
    UpgradeId.BANSHEESPEED: UnitTypeId.STARPORTTECHLAB,
    UpgradeId.BATTLECRUISERENABLESPECIALIZATIONS: UnitTypeId.FUSIONCORE,
    UpgradeId.BLINKTECH: UnitTypeId.TWILIGHTCOUNCIL,
    UpgradeId.BURROW: UnitTypeId.HATCHERY,
    UpgradeId.CENTRIFICALHOOKS: UnitTypeId.BANELINGNEST,
    UpgradeId.CHARGE: UnitTypeId.TWILIGHTCOUNCIL,
    UpgradeId.CHITINOUSPLATING: UnitTypeId.ULTRALISKCAVERN,
    UpgradeId.CYCLONELOCKONDAMAGEUPGRADE: UnitTypeId.FACTORYTECHLAB,
    UpgradeId.DARKTEMPLARBLINKUPGRADE: UnitTypeId.DARKSHRINE,
    UpgradeId.DIGGINGCLAWS: UnitTypeId.LURKERDENMP,
    UpgradeId.DRILLCLAWS: UnitTypeId.FACTORYTECHLAB,
    UpgradeId.ENHANCEDSHOCKWAVES: UnitTypeId.INFESTATIONPIT,
    UpgradeId.EVOLVEGROOVEDSPINES: UnitTypeId.HYDRALISKDEN,
    UpgradeId.EVOLVEMUSCULARAUGMENTS: UnitTypeId.HYDRALISKDEN,
    UpgradeId.EXTENDEDTHERMALLANCE: UnitTypeId.ROBOTICSBAY,
    UpgradeId.GLIALRECONSTITUTION: UnitTypeId.ROACHWARREN,
    UpgradeId.GRAVITICDRIVE: UnitTypeId.ROBOTICSBAY,
    UpgradeId.HIGHCAPACITYBARRELS: UnitTypeId.FACTORYTECHLAB,
    UpgradeId.HISECAUTOTRACKING: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.INFESTORENERGYUPGRADE: UnitTypeId.INFESTATIONPIT,
    UpgradeId.LIBERATORAGRANGEUPGRADE: UnitTypeId.FUSIONCORE,
    UpgradeId.LURKERRANGE: UnitTypeId.LURKERDENMP,
    UpgradeId.MEDIVACINCREASESPEEDBOOST: UnitTypeId.FUSIONCORE,
    UpgradeId.NEURALPARASITE: UnitTypeId.INFESTATIONPIT,
    UpgradeId.OBSERVERGRAVITICBOOSTER: UnitTypeId.ROBOTICSBAY,
    UpgradeId.OVERLORDSPEED: UnitTypeId.HATCHERY,
    UpgradeId.PERSONALCLOAKING: UnitTypeId.GHOSTACADEMY,
    UpgradeId.PHOENIXRANGEUPGRADE: UnitTypeId.FLEETBEACON,
    UpgradeId.PROTOSSAIRARMORSLEVEL1: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.PROTOSSAIRARMORSLEVEL2: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.PROTOSSAIRARMORSLEVEL3: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.PROTOSSAIRWEAPONSLEVEL1: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.PROTOSSAIRWEAPONSLEVEL2: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.PROTOSSAIRWEAPONSLEVEL3: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL1: UnitTypeId.FORGE,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL2: UnitTypeId.FORGE,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL3: UnitTypeId.FORGE,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1: UnitTypeId.FORGE,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2: UnitTypeId.FORGE,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3: UnitTypeId.FORGE,
    UpgradeId.PROTOSSSHIELDSLEVEL1: UnitTypeId.FORGE,
    UpgradeId.PROTOSSSHIELDSLEVEL2: UnitTypeId.FORGE,
    UpgradeId.PROTOSSSHIELDSLEVEL3: UnitTypeId.FORGE,
    UpgradeId.PSISTORMTECH: UnitTypeId.TEMPLARARCHIVE,
    UpgradeId.PUNISHERGRENADES: UnitTypeId.BARRACKSTECHLAB,
    UpgradeId.RAVENCORVIDREACTOR: UnitTypeId.STARPORTTECHLAB,
    UpgradeId.SHIELDWALL: UnitTypeId.BARRACKSTECHLAB,
    UpgradeId.SMARTSERVOS: UnitTypeId.FACTORYTECHLAB,
    UpgradeId.STIMPACK: UnitTypeId.BARRACKSTECHLAB,
    UpgradeId.TEMPESTGROUNDATTACKUPGRADE: UnitTypeId.GHOSTACADEMY,
    UpgradeId.TERRANBUILDINGARMOR: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANINFANTRYARMORSLEVEL1: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANINFANTRYARMORSLEVEL2: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANINFANTRYARMORSLEVEL3: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANINFANTRYWEAPONSLEVEL1: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANINFANTRYWEAPONSLEVEL2: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANINFANTRYWEAPONSLEVEL3: UnitTypeId.ENGINEERINGBAY,
    UpgradeId.TERRANSHIPWEAPONSLEVEL1: UnitTypeId.ARMORY,
    UpgradeId.TERRANSHIPWEAPONSLEVEL2: UnitTypeId.ARMORY,
    UpgradeId.TERRANSHIPWEAPONSLEVEL3: UnitTypeId.ARMORY,
    UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1: UnitTypeId.ARMORY,
    UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2: UnitTypeId.ARMORY,
    UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3: UnitTypeId.ARMORY,
    UpgradeId.TERRANVEHICLEWEAPONSLEVEL1: UnitTypeId.ARMORY,
    UpgradeId.TERRANVEHICLEWEAPONSLEVEL2: UnitTypeId.ARMORY,
    UpgradeId.TERRANVEHICLEWEAPONSLEVEL3: UnitTypeId.ARMORY,
    UpgradeId.TUNNELINGCLAWS: UnitTypeId.ROACHWARREN,
    UpgradeId.VOIDRAYSPEEDUPGRADE: UnitTypeId.FLEETBEACON,
    UpgradeId.WARPGATERESEARCH: UnitTypeId.CYBERNETICSCORE,
    UpgradeId.ZERGFLYERARMORSLEVEL1: UnitTypeId.SPIRE,
    UpgradeId.ZERGFLYERARMORSLEVEL2: UnitTypeId.SPIRE,
    UpgradeId.ZERGFLYERARMORSLEVEL3: UnitTypeId.SPIRE,
    UpgradeId.ZERGFLYERWEAPONSLEVEL1: UnitTypeId.SPIRE,
    UpgradeId.ZERGFLYERWEAPONSLEVEL2: UnitTypeId.SPIRE,
    UpgradeId.ZERGFLYERWEAPONSLEVEL3: UnitTypeId.SPIRE,
    UpgradeId.ZERGGROUNDARMORSLEVEL1: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGGROUNDARMORSLEVEL2: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGGROUNDARMORSLEVEL3: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGLINGATTACKSPEED: UnitTypeId.SPAWNINGPOOL,
    UpgradeId.ZERGLINGMOVEMENTSPEED: UnitTypeId.SPAWNINGPOOL,
    UpgradeId.ZERGMELEEWEAPONSLEVEL1: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMELEEWEAPONSLEVEL2: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMELEEWEAPONSLEVEL3: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL1: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL2: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL3: UnitTypeId.EVOLUTIONCHAMBER,
}
