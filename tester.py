from free_rooms.finder import planFreeRooms

for plan in planFreeRooms("10:00", "17:00", buildings_filter=["eng"]):
    print(plan["slot"])
    print( [room.name for room in plan["rooms"]] ) 
