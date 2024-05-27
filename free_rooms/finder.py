from typing import Optional
import requests
from datetime import datetime
import pytz
from .Room import Room


calendar_ids = {
    "ingegneria": "5e9996a228a649001237296d"
}

building_to_ids = {
    "eng": [ "5dc3ed5c74895700123a91aa", "5dc3ed5c74895700123a91ac", "5dc3ed5c74895700123a91a8", "5dc3ed5c74895700123a91a6" ],
    "chem": [ "5dc3ed5a74895700123a90aa", "5dc3ed5974895700123a906c" ],
    "math": [ "5dc3ed5c74895700123a916c" ],
    "arch": [ "5dc3ed5c74895700123a9184" ]
}
id_to_building = {
    id: building for building, ids in building_to_ids.items() for id in ids 
}

BUILDINGS = sorted([ *building_to_ids.keys() ])


def __getRoomIds(calendar_id:str="5e9996a228a649001237296d") -> list[str]:
    """
        Gets the room ids associated to a calendar id.

        Parameters
        ----------
            calendar_id : str
        
        Returns
        -------
            room_ids : list[str]
                List of the room ids.
    """
    url = f"https://unibo.prod.up.cineca.it/api/LinkCalendario/searchCalendarioPubblico?filter[clienteId]=5ad08435b6ca5357dbac609e&linkCalendarioId={calendar_id}"
    requests.post(url)
    calendar_info_json = requests.post(url).json()

    return calendar_info_json["payload"]["aule"]


def __getTimeTable(year:int, month:int, day:int, calendar_id:str="5e9996a228a649001237296d") -> list[Room]:
    """
        Gets the room information associated to a calendar id.

        Parameters
        ----------
            year, month, day : int
                Year, month, and day to query.

            calendar_id : str

        Returns
        -------
            rooms : list[Room]
                List of the rooms.
    """
    url = (
        "https://unibo.prod.up.cineca.it/api/Impegni/getImpegniCalendarioPubblico" + 
        "?mostraImpegniAnnullati=false" +
        "&mostraIndisponibilitaTotali=false" +
        f"&linkCalendarioId={calendar_id}" + 
        "&clienteId=5ad08435b6ca5357dbac609e" + 
        "&pianificazioneTemplate=false" + 
        # "".join([f"&auleIds[]={room_id}" for room_id in __getRoomIds()]) +
        "&limitaRisultati=false" + 
        f"&dataInizio={year}-{month:>02}-{day:>02}T00:00:00.000Z" + 
        f"&dataFine={year}-{month:>02}-{day:>02}T22:59:59.999Z"
    )
    timetable_json = requests.post(url).json()
    rooms = {}

    for lesson in timetable_json:
        lesson_start = pytz.UTC.localize( datetime.strptime(lesson["dataInizio"], "%Y-%m-%dT%H:%M:%S.%fZ") )
        lesson_end = pytz.UTC.localize( datetime.strptime(lesson["dataFine"], "%Y-%m-%dT%H:%M:%S.%fZ") )
        room_id, room_name, room_building = None, None, None

        if lesson["notaSospensione"] is not None: continue # Cancelled lesson

        # Searches room info
        for resource in lesson["risorse"]:
            if resource["aulaId"] is not None:
                room_id = resource["aulaId"]
                room_name = resource["aula"]["descrizione"]
                building_id = resource["aula"]["edificioId"]
                if "edificioId" in resource["aula"]:
                    room_building = id_to_building[building_id] if building_id in id_to_building else building_id
                break
        
        if room_id is not None:
            if room_id not in rooms: rooms[room_id] = Room(room_id, room_name, room_building)
            rooms[room_id].lessons.append( (lesson_start, lesson_end) )
        
    return rooms


def __intervalsIntersect(interval1:tuple, interval2:tuple):
    """
        Checks if two intervals are intersecting.

        Parameters
        ----------
            interval1, interval2 : tuple[Comparable, Comparable]
                The intervals to compare

        Returns
        -------
            are_intersecting : bool
    """
    start1, end1 = interval1
    start2, end2 = interval2

    return (
        (start2 <= start1 < end2) or
        (start2 < end1 <= end2) or
        (start1 <= start2 and end1 >= end2)
    )


def searchFreeRooms(
        start_time: str, 
        end_time: str, 
        year: Optional[int] = None, 
        month: Optional[int] = None, 
        day: Optional[int] = None, 
        campus: str = "ingegneria",
        buildings_filter: Optional[list[str]] = None
    ) -> list[Room]:
    """
        Finds the rooms that are free in a given time slot.

        Parameters
        ----------
            start_time, end_time : str (hh:mm)
                Start and end time to query for the free rooms.
                hh:mm format.

            year, month, day : int|None
                Year, month, and day to query.

            campus : str
                Campus in which the rooms are searched.

        Returns
        -------
            free_rooms : list[Room]
                List of free rooms.
    """
    if year is None or month is None or day is None:
        now = datetime.now()
        year, month, day = now.year, now.month, now.day

    free_rooms = []
    slot_start = pytz.timezone("Europe/Rome").localize( datetime(year, month, day, int(start_time.split(":")[0]), int(start_time.split(":")[1])) )
    slot_end = pytz.timezone("Europe/Rome").localize( datetime(year, month, day, int(end_time.split(":")[0]), int(end_time.split(":")[1])) )

    rooms = __getTimeTable(year, month, day, calendar_ids[campus])

    # Looks for free rooms
    for room in rooms.values():
        is_room_free = True
        for lesson_start, lesson_end in room.lessons:
            if __intervalsIntersect( (slot_start, slot_end), (lesson_start, lesson_end) ):
                is_room_free = False
                break

        is_correct_building = (buildings_filter is None) or (room.building in buildings_filter)
        
        if is_room_free and is_correct_building: free_rooms.append(room)

    free_rooms.sort(key=lambda r: (r.building, r.name))
    return free_rooms