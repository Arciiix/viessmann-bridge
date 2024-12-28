import asyncio
from datetime import datetime, timedelta
from viessmann_bridge.config import get_actions, get_config
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

            for action in get_actions():
                # Convert the array of daily values to a dictionary with dates
                # The day_readat is the date of the last value in the array
                # The next values are for previous days (day_readat - 1, day_readat - 2, etc.)
                daily_values = {
                    ctx.gas_consumption.day_readat.date()
                    - timedelta(days=i): ctx.gas_consumption.day[i]
                    for i in range(len(ctx.gas_consumption.day))
                }

                logger.debug(f"Daily values: {daily_values}")

                await action.update_daily_consumption_stats(ctx, daily_values)
                await action.update_current_total_consumption(
                    ctx, ctx.total_consumption
                )

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

            await asyncio.gather(
                *[
                    action.update_current_total_consumption(ctx, ctx.total_consumption)
                    for action in get_actions()
                ]
            )

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

            ctx.previous_consumption_date = ctx.gas_consumption.day_readat.date()
            ctx.previous_consumption_daily = ctx.gas_consumption.day

            # Since the current day value didn't exist before, we just add the current day's value to the total (which is equal to the offset)
            new_offset = ctx.gas_consumption.day[0]
            ctx.total_consumption += new_offset
            logger.info(f"New day's consumption: {new_offset} m3")

            await asyncio.gather(
                *[
                    action.handle_consumption_midnight_case(
                        ctx,
                        counter_offset,
                        current_previous_day,
                        ctx.gas_consumption.day[0],
                        ctx.total_consumption,
                    )
                    for action in get_actions()
                ]
            )

    async def main_loop(self):
        logger.info("Starting working")
        config = get_config()
        while True:
            logger.debug("Sleeping")
            await asyncio.sleep(config.sleep_interval_seconds)
            logger.info(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --")

            # No concurrent calls because some of the actions might not be thread-safe
            await self.handle_gas_usage()

            logger.info("All tasks done")
