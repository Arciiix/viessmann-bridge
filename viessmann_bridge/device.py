from datetime import datetime
from PyViCare.PyViCareGazBoiler import GazBoiler

from viessmann_bridge.consumption import Consumption
from viessmann_bridge.utils import parse_time


class Device(GazBoiler):
    def get_gas_usage(self):
        raw_consumption = self.service.getProperty("heating.gas.consumption.heating")

        consumption_parsed = Consumption(
            timestamp=datetime.fromisoformat(raw_consumption["timestamp"]["value"]),
            day=raw_consumption["properties"]["day"]["value"],
            week=raw_consumption["properties"]["week"]["value"],
            month=raw_consumption["properties"]["month"]["value"],
            year=raw_consumption["properties"]["year"]["value"],
            day_readat=parse_time(raw_consumption["dayValueReadAt"]["value"]),
            week_readat=parse_time(raw_consumption["weekValueReadAt"]["value"]),
            month_readat=parse_time(raw_consumption["monthValueReadAt"]["value"]),
            year_readat=parse_time(raw_consumption["yearValueReadAt"]["value"]),
        )

        return consumption_parsed
