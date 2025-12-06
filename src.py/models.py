
class MeterReading:
    def __init__(self, timestamp, kwh: float):
        self.timestamp = timestamp
        self.kwh = kwh

class Building:
    def __init__(self, name: str):
        self.name = name
        self.meter_readings = []

    def add_reading(self, reading: MeterReading):
        self.meter_readings.append(reading)

    def calculate_total_consumption(self) -> float:
        return sum(r.kwh for r in self.meter_readings)

    def generate_report(self) -> str:
        total = self.calculate_total_consumption()
        count = len(self.meter_readings)
        avg = total / count if count else 0
        return f"Building {self.name}: total={total:.2f} kWh, avg={avg:.2f} kWh over {count} readings"

class BuildingManager:
    def __init__(self):
        self.buildings = {}

    def get_or_create_building(self, name: str) -> Building:
        if name not in self.buildings:
            self.buildings[name] = Building(name)
        return self.buildings[name]

    def add_reading(self, building_name: str, reading: MeterReading):
        bld = self.get_or_create_building(building_name)
        bld.add_reading(reading)
