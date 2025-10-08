from dataclasses import dataclass

@dataclass
class SimulatorState:
    temperatureC: float
    targetTemp: float
    lightOn: bool
    pause_until: float  # epoch seconds until which to pause publishing
