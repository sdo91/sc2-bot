from sc2.ids.unit_typeid import UnitTypeId



class Wave(object):

    units: [UnitTypeId] = []

    def do(self):
        self.move()
        self.prioritize_targets()

    def prioritize_targets(self):
        pass

    def move(self):
        pass
