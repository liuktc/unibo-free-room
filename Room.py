class Room:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.lessons = []

    def __str__(self):
        return f"{self.id} {self.name} {self.lessons}"