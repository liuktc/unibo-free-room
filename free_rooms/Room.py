class Room:
    def __init__(self, id, name, building, has_plugs):
        self.id = id
        self.name = name
        self.building = building
        self.lessons = []
        self.has_plugs = has_plugs

    def __str__(self):
        return f"{self.id} {self.name} {self.lessons} {'yes_plugs' if self.has_plugs else 'no_plugs'}"