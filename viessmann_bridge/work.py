import asyncio
from datetime import date
from typing import Optional
from viessmann_bridge.consumption import Consumption
from viessmann_bridge.device import Device
from viessmann_bridge.logger import logger


class ViessmannBridge:
    # Gas usage
    gas_consumption: Optional[Consumption] = None
    total_consumption: int = 0  # TODO: Maybe fetch it from Domoticz or something?
    previous_consumption_daily: list[int] = []
    previous_consumption_date: Optional[date] = None

    def __init__(self, device: Device):
        self.device = device

    async def handle_gas_usage(self):
        self.gas_consumption = self.device.get_gas_usage()

        # If it's the first run, let's just update the daily values
        if self.previous_consumption_date is None:
            self.previous_consumption_date = self.gas_consumption.day_readat.date()
            self.previous_consumption_daily = self.gas_consumption.day
            self.total_consumption = sum(self.gas_consumption.year)

            # TODO: Update the historical values for the previous days in Domoticz
            # TODO: Also, if the previous total is different from the current one, update it

            return

        # If a new day didn't start, we just update the current value
        if (
            self.previous_consumption_date == self.gas_consumption.day_readat.date()
            and self.previous_consumption_daily[-1] == self.gas_consumption.day[-1]
        ):
            previous_total_daily = sum(self.previous_consumption_daily)
            current_total_daily = sum(self.gas_consumption.day)

            counter_offset = current_total_daily - previous_total_daily
            self.total_consumption += counter_offset

            logger.debug(
                f"Previous daily array: {self.previous_consumption_daily}, current daily array: {self.gas_consumption.day}"
            )

            self.previous_consumption_daily = self.gas_consumption.day

            # TODO: Send to Domoticz/HomeAssistant
            logger.info(
                f"Total consumption: {self.total_consumption} m3 (offset: {counter_offset} m3). Sum of daily: {self.gas_consumption.day} m3"
            )

            return
        else:
            # If a new day started
            logger.info("New day started")

            # Update the historical value for the previous day
            current_previous_day = self.gas_consumption.day[1]
            previous_previous_day = self.previous_consumption_daily[0]

            counter_offset = current_previous_day - previous_previous_day
            self.total_consumption += counter_offset

            logger.info(
                f"The previous day's consumption - previous: {previous_previous_day} m3, current: {current_previous_day} m3, offset: {counter_offset} m3"
            )

            # TODO: Update the historical values for the day

            self.previous_consumption_date = self.gas_consumption.day_readat.date()
            self.previous_consumption_daily = self.gas_consumption.day

            # Since the current day value didn't exist before, we just add the current day's value to the total (which is equal to the offset)
            new_offset = self.gas_consumption.day[0]
            self.total_consumption += new_offset
            logger.info(f"New day's consumption: {new_offset} m3")

            # TODO: Update current day value (just the counter now)

    async def main_loop(self):
        logger.info("Starting working")
        while True:
            # TODO: Better sleep
            await asyncio.sleep(10)

            tasks = [self.handle_gas_usage()]
            await asyncio.gather(*tasks)
            logger.info("All tasks done")
