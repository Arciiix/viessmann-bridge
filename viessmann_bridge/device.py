from datetime import datetime
from PyViCare.PyViCareGazBoiler import GazBoiler
from PyViCare.PyViCareService import ViCareService

from viessmann_bridge.consumption import Consumption
from viessmann_bridge.utils import parse_time


class Device(GazBoiler):
    def __init__(self, boiler: GazBoiler) -> None:
        super().__init__(boiler.service)

    def get_gas_usage(self):
        raw_consumption = self.service.getProperty("heating.gas.consumption.total")

        consumption_parsed = Consumption(
            timestamp=datetime.fromisoformat(raw_consumption["timestamp"]),
            day=raw_consumption["properties"]["day"]["value"],
            week=raw_consumption["properties"]["week"]["value"],
            month=raw_consumption["properties"]["month"]["value"],
            year=raw_consumption["properties"]["year"]["value"],
            day_readat=parse_time(
                raw_consumption["properties"]["dayValueReadAt"]["value"]
            ),
            week_readat=parse_time(
                raw_consumption["properties"]["weekValueReadAt"]["value"]
            ),
            month_readat=parse_time(
                raw_consumption["properties"]["monthValueReadAt"]["value"]
            ),
            year_readat=parse_time(
                raw_consumption["properties"]["yearValueReadAt"]["value"]
            ),
        )

        return consumption_parsed

    def get_burners_modulations(self, number_of_burners: int) -> list[int]:
        modulations: list[int] = []

        for i in range(number_of_burners):
            raw_modulation = self.service.getProperty(f"heating.burners.{i}.modulation")
            modulations.append(raw_modulation["properties"]["value"]["value"])

        return modulations
