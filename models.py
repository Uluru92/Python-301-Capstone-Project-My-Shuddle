from dataclasses import dataclass
from datetime import datetime

@dataclass
class BusLocation:
    bus_id: str
    lat: float
    lng: float
    timestamp: str  # ISO format

    def to_dict(self):
        return {
            "bus_id": self.bus_id,
            "lat": self.lat,
            "lng": self.lng,
            "timestamp": self.timestamp,
        }

class BusTracker:
    def __init__(self):
        self.coords_by_bus = {}

    def add_location(self, bus_id: str, lat: float, lng: float, timestamp: str = None):
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        location = BusLocation(bus_id, lat, lng, timestamp)
        self.coords_by_bus.setdefault(bus_id, []).append(location)

    def get_all_locations(self):
        return self.coords_by_bus

    def get_latest_location(self, bus_id: str):
        if bus_id in self.coords_by_bus and self.coords_by_bus[bus_id]:
            return self.coords_by_bus[bus_id][-1]
        return None