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
        ctx.previous_total_consumption = ctx.total_consumption

        ctx.gas_consumption = self.device.get_gas_usage()

        # Bugfix: sometimes the daily values are not updated and the data is nonsense (happened to me once)
        # Check if either:
        # - the daily values are not the same as the previous daily values (excluding the first value)
        # - the daily values are not the same as the previous daily values but with offset of 1 (a new day can appear in new values)
        #
        if (
            ctx.previous_consumption_daily is not None
            and ctx.previous_consumption_daily[1:] != ctx.gas_consumption.day[1:]
            and ctx.previous_consumption_daily[1:-1] != ctx.gas_consumption.day[2:]
        ):
            logger.error(
                f"Daily values are weird: previous: {ctx.previous_consumption_daily}, current: {ctx.gas_consumption.day}. Skipping updating gas..."
            )
            return

        # If it's the first run, let's just update the daily values
        if ctx.previous_consumption_date is None:
            ctx.previous_consumption_date = ctx.gas_consumption.day_readat.date()
            ctx.previous_consumption_daily = ctx.gas_consumption.day
            ctx.total_consumption = sum(ctx.gas_consumption.year)

            # TODO: Maybe fetch the previous total consumption from the action (Domoticz/Home Assistant) instead?
            ctx.previous_total_consumption = ctx.total_consumption

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
                    ctx, ctx.total_consumption, ctx.gas_consumption.day[0]
                )
                await action.update_current_total_consumption_increasing(ctx, 0)

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
                    action.update_current_total_consumption(
                        ctx, ctx.total_consumption, ctx.gas_consumption.day[0]
                    )
                    for action in get_actions()
                ]
            )

            await asyncio.gather(
                *[
                    action.update_current_total_consumption_increasing(
                        ctx, ctx.total_consumption - ctx.previous_total_consumption
                    )
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

            if counter_offset < 0:
                logger.warning(
                    f"Counter offset is negative: {counter_offset}. Previous day: {previous_previous_day}, current day: {current_previous_day}"
                )
                counter_offset = 0

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

    async def handle_burners(self):
        config = get_config()
        burners_modulations = self.device.get_burners_modulations(
            config.number_of_burners
        )
        logger.info(f"Burners modulations: {burners_modulations}%")

        for action in get_actions():
            await action.handle_burners_modulations(burners_modulations)

    async def handle_boiler_temperature(self):
        boiler_temperature = self.device.get_boiler_temperature()
        logger.info(f"Boiler temperature: {boiler_temperature}°C")

        for action in get_actions():
            await action.handle_boiler_temperature(boiler_temperature)

    async def main_loop(self):
        logger.info("Starting working")
        config = get_config()

        logger.debug("Sleeping 10 seconds before start")
        await asyncio.sleep(10)

        while True:
            logger.info(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --")

            # No concurrent calls because some of the actions might not be thread-safe
            await self.handle_gas_usage()
            await self.handle_burners()
            await self.handle_boiler_temperature()

            logger.info("All tasks done")
            await asyncio.sleep(config.sleep_interval_seconds)
