import asyncio
from viessmann_bridge.consumption import ConsumptionContext
from viessmann_bridge.device import Device
from viessmann_bridge.logger import logger


class ViessmannBridge:
    consumption_context: ConsumptionContext = ConsumptionContext()

    def __init__(self, device: Device):
        self.device = device

    async def handle_gas_usage(self):
        ctx = self.consumption_context

        ctx.gas_consumption = self.device.get_gas_usage()

        # If it's the first run, let's just update the daily values
        if ctx.previous_consumption_date is None:
            ctx.previous_consumption_date = ctx.gas_consumption.day_readat.date()
            ctx.previous_consumption_daily = ctx.gas_consumption.day
            ctx.total_consumption = sum(ctx.gas_consumption.year)

            # TODO: Update the historical values for the previous days in Domoticz
            # TODO: Also, if the previous total is different from the current one, update it

            return

        # If a new day didn't start, we just update the current value
        if (
            ctx.previous_consumption_date == ctx.gas_consumption.day_readat.date()
            and ctx.previous_consumption_daily[-1] == ctx.gas_consumption.day[-1]
        ):
            previous_total_daily = sum(ctx.previous_consumption_daily)
            current_total_daily = sum(ctx.gas_consumption.day)

            counter_offset = current_total_daily - previous_total_daily
            ctx.total_consumption += counter_offset

            logger.debug(
                f"Previous daily array: {ctx.previous_consumption_daily}, current daily array: {ctx.gas_consumption.day}"
            )

            ctx.previous_consumption_daily = ctx.gas_consumption.day

            # TODO: Send to Domoticz/HomeAssistant
            logger.info(
                f"Total consumption: {ctx.total_consumption} m3 (offset: {counter_offset} m3). Sum of daily: {ctx.gas_consumption.day} m3"
            )

            return
        else:
            # If a new day started
            logger.info("New day started")

            # Update the historical value for the previous day
            current_previous_day = ctx.gas_consumption.day[1]
            previous_previous_day = ctx.previous_consumption_daily[0]

            counter_offset = current_previous_day - previous_previous_day
            ctx.total_consumption += counter_offset

            logger.info(
                f"The previous day's consumption - previous: {previous_previous_day} m3, current: {current_previous_day} m3, offset: {counter_offset} m3"
            )

            # TODO: Update the historical values for the day

            ctx.previous_consumption_date = ctx.gas_consumption.day_readat.date()
            ctx.previous_consumption_daily = ctx.gas_consumption.day

            # Since the current day value didn't exist before, we just add the current day's value to the total (which is equal to the offset)
            new_offset = ctx.gas_consumption.day[0]
            ctx.total_consumption += new_offset
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
