class Student:
    ''''Info about Students'''
    def __init__(self, student_id, name):
        self.student_id = student_id
        self.name = name

class Bus:
    '''Info about Bus'''
    def __init__(self, bus_id):
        self.bus_id = bus_id
        self.locations = [] # list of locations
        self.students_onboard = []  # list of students inside the bus

    def add_location(self, lat, lng, timestamp):
        loc = BusLocation(self.bus_id, lat, lng, timestamp)
        self.locations.append(loc)

    def latest_location(self):
        return self.locations[-1] if self.locations else None
    
    def board_student(self, student: Student):
        if student not in self.students_onboard:
            self.students_onboard.append(student)
            print(f"{student.name} boarded {self.bus_id}")

    def list_students(self):
        return [s.name for s in self.students_onboard]

class BusLocation:
    '''Info about every point location received'''
    def __init__(self, bus_id, lat, lng, timestamp):
        self.bus_id = bus_id
        self.lat = lat
        self.lng = lng
        self.timestamp = timestamp

    def __repr__(self):
        return f"BusLocation(bus_id={self.bus_id}, lat={self.lat}, lng={self.lng}, timestamp={self.timestamp})"

    def to_dict(self):
        return {
            "bus_id": self.bus_id,
            "lat": self.lat,
            "lng": self.lng,
            "timestamp": self.timestamp,
        }

class BusTracker:
    '''Info about all coords from a bus'''
    def __init__(self):
        self.coords_by_bus = {}

    def add_location(self, bus_id: str, lat: float, lng: float, timestamp: str = None):
        location = BusLocation(bus_id, lat, lng, timestamp)
        self.coords_by_bus.setdefault(bus_id, []).append(location)

    def get_all_locations(self):
        return self.coords_by_bus

    def get_latest_location(self, bus_id: str):
        if bus_id in self.coords_by_bus and self.coords_by_bus[bus_id]:
            return self.coords_by_bus[bus_id][-1]
        return None


