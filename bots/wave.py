from sc2.ids.unit_typeid import UnitTypeId

class Wave(object):

    loc = None
    def __init__(self, location):
        self.loc = location

    units: [UnitTypeId] = []

    def do(self):
        self.move()
        self.prioritize_targets()

    def prioritize_targets(self):
        pass

    def move(self):
        for unit in self.units:
            unit.attack(self.loc)

