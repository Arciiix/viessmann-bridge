import asyncio
from viessmann_bridge.consumption import ConsumptionContext
from viessmann_bridge.device import Device
from viessmann_bridge.logger import logger


class ViessmannBridge:
    consumption_context: ConsumptionContext = ConsumptionContext()

    def __init__(self, device: Device):
        self.device = device

    async def handle_gas_usage(self):
        gas_consumption = self.device.get_gas_usage()
        previous_consumption_date = self.consumption_context.previous_consumption_date
        previous_consumption_daily = self.consumption_context.previous_consumption_daily
        total_consumption = self.consumption_context.total_consumption

        # If it's the first run, let's just update the daily values
        if previous_consumption_date is None:
            previous_consumption_date = gas_consumption.day_readat.date()
            previous_consumption_daily = gas_consumption.day
            total_consumption = sum(gas_consumption.year)

            # TODO: Update the historical values for the previous days in Domoticz
            # TODO: Also, if the previous total is different from the current one, update it

            self.consumption_context = ConsumptionContext(
                gas_consumption=gas_consumption,
                total_consumption=total_consumption,
                previous_consumption_daily=previous_consumption_daily,
                previous_consumption_date=previous_consumption_date,
            )
            return

        # If a new day didn't start, we just update the current value
        if (
            previous_consumption_date == gas_consumption.day_readat.date()
            and previous_consumption_daily[-1] == gas_consumption.day[-1]
        ):
            previous_total_daily = sum(previous_consumption_daily)
            current_total_daily = sum(gas_consumption.day)

            counter_offset = current_total_daily - previous_total_daily
            total_consumption += counter_offset

            logger.debug(
                f"Previous daily array: {previous_consumption_daily}, current daily array: {gas_consumption.day}"
            )

            previous_consumption_daily = gas_consumption.day

            # TODO: Send to Domoticz/HomeAssistant
            logger.info(
                f"Total consumption: {total_consumption} m3 (offset: {counter_offset} m3). Sum of daily: {gas_consumption.day} m3"
            )

            self.consumption_context = ConsumptionContext(
                gas_consumption=gas_consumption,
                total_consumption=total_consumption,
                previous_consumption_daily=previous_consumption_daily,
                previous_consumption_date=previous_consumption_date,
            )

            return
        else:
            # If a new day started
            logger.info("New day started")

            # Update the historical value for the previous day
            current_previous_day = gas_consumption.day[1]
            previous_previous_day = previous_consumption_daily[0]

            counter_offset = current_previous_day - previous_previous_day
            total_consumption += counter_offset

            logger.info(
                f"The previous day's consumption - previous: {previous_previous_day} m3, current: {current_previous_day} m3, offset: {counter_offset} m3"
            )

            # TODO: Update the historical values for the day

            previous_consumption_date = gas_consumption.day_readat.date()
            previous_consumption_daily = gas_consumption.day

            # Since the current day value didn't exist before, we just add the current day's value to the total (which is equal to the offset)
            new_offset = gas_consumption.day[0]
            total_consumption += new_offset
            logger.info(f"New day's consumption: {new_offset} m3")

            # TODO: Update current day value (just the counter now)

            self.consumption_context = ConsumptionContext(
                gas_consumption=gas_consumption,
                total_consumption=total_consumption,
                previous_consumption_daily=previous_consumption_daily,
                previous_consumption_date=previous_consumption_date,
            )

    async def main_loop(self):
        logger.info("Starting working")
        while True:
            # TODO: Better sleep
            await asyncio.sleep(10)

            tasks = [self.handle_gas_usage()]
            await asyncio.gather(*tasks)
            logger.info("All tasks done")
