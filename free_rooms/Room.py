class Room:
    def __init__(self, id, name, building):
        self.id = id
        self.name = name
        self.building = building
        self.lessons = []

    def __str__(self):
        return f"{self.id} {self.name} {self.lessons}"