import asyncio
from datetime import date
from math import floor

from viessmann_bridge.action import Action
from viessmann_bridge.config import DomoticzActionConfig
from viessmann_bridge.consumption import ConsumptionContext
from viessmann_bridge.logger import logger
import aiohttp

from viessmann_bridge.utils import gas_consumption_kwh_to_m3


class Domoticz(Action):
    config: DomoticzActionConfig

    def __init__(self, config: DomoticzActionConfig) -> None:
        self.config = config

    async def _request(self, params: dict) -> None:
        logger.debug(
            f"Requesting Domoticz {self.config.domoticz_url} with params {params}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.config.domoticz_url}/json.htm", params=params
            ) as response:
                if response.status == 200:
                    logger.debug(f"Response: {await response.text()}")
                else:
                    logger.error(
                        f"Failed to request Domoticz {self.config.domoticz_url}: {response.status}"
                    )

    def _consumption_to_m3(self, consumption: int) -> int:
        return floor(gas_consumption_kwh_to_m3(consumption) * 1000)

    async def init(self) -> None:
        pass

    async def update_current_total_consumption(
        self,
        consumption_context: ConsumptionContext,
        total_consumption: int,
    ) -> None:
        logger.debug(f"Updating current total consumption: {total_consumption}")

        if self.config.gas_consumption_kwh_idx is not None:
            await self._request(
                {
                    "type": "command",
                    "param": "udevice",
                    "idx": self.config.gas_consumption_kwh_idx,
                    "nvalue": 0,
                    "svalue": str(total_consumption),
                }
            )

        if self.config.gas_consumption_m3_idx is not None:
            await self._request(
                {
                    "type": "command",
                    "param": "udevice",
                    "idx": self.config.gas_consumption_m3_idx,
                    "nvalue": 0,
                    "svalue": str(self._consumption_to_m3(total_consumption)),
                }
            )

        logger.debug(f"Updated current total consumption: {total_consumption}")

    async def update_daily_consumption_stats(
        self, consumption_context: ConsumptionContext, consumption: dict[date, int]
    ):
        logger.debug(f"Updating daily consumption stats: {consumption}")

        requests = []

        for day, value in consumption.items():
            if self.config.gas_consumption_kwh_idx is not None:
                requests.append(
                    self._request(
                        {
                            "type": "command",
                            "param": "udevice",
                            "idx": self.config.gas_consumption_kwh_idx,
                            "nvalue": 0,
                            "svalue": f"{str(value * 1000)};0;{day.strftime('%Y-%m-%d')}",
                        }
                    )
                )

            if self.config.gas_consumption_m3_idx is not None:
                requests.append(
                    self._request(
                        {
                            "type": "command",
                            "param": "udevice",
                            "idx": self.config.gas_consumption_m3_idx,
                            "nvalue": 0,
                            "svalue": f"{str(self._consumption_to_m3(value))};0;{day.strftime('%Y-%m-%d')}",
                        }
                    )
                )

        await asyncio.gather(*requests)

        logger.debug(f"Updated daily consumption stats: {consumption}")

    async def update_consumption_point_in_time(
        self,
        consumption_context: ConsumptionContext,
        point_in_time: date,
        value: int,
    ):
        logger.debug(f"Updating consumption at {point_in_time}: {value}")

        if self.config.gas_consumption_kwh_idx is not None:
            await self._request(
                {
                    "type": "command",
                    "param": "udevice",
                    "idx": self.config.gas_consumption_kwh_idx,
                    "nvalue": 0,
                    "svalue": f"{str(value * 1000)};0;{point_in_time.strftime('%Y-%m-%d %H:%M:%S')}",
                }
            )

        if self.config.gas_consumption_m3_idx is not None:
            await self._request(
                {
                    "type": "command",
                    "param": "udevice",
                    "idx": self.config.gas_consumption_m3_idx,
                    "nvalue": 0,
                    "svalue": f"{str(self._consumption_to_m3(value))};0;{point_in_time.strftime('%Y-%m-%d %H:%M:%S')}",
                }
            )

        logger.debug(f"Updated consumption at {point_in_time}: {value}")

    async def handle_consumption_midnight_case(
        self,
        consumption_context: ConsumptionContext,
        previous_day_new_value: int,
        offset_previous_day: int,
        current_day_value: int,
        total_counter: int,
    ):
        logger.debug(f"""
Handling midnight case with the following values:
    previous_day_new_value: {previous_day_new_value},
    offset_previous_day: {offset_previous_day},
    current_day_value: {current_day_value},
    total_counter: {total_counter}
""")
        assert consumption_context.previous_consumption_date is not None

        await self.update_daily_consumption_stats(
            consumption_context,
            {
                consumption_context.previous_consumption_date: previous_day_new_value,
                date.today(): current_day_value,
            },
        )

        await self.update_current_total_consumption(consumption_context, total_counter)

        # Now let's add a historical log entry for the 23:59 value of the previous day
        # so that the total consumption is correct for the previous day
        # (it's not counted as for 'today', but for 'yesterday')
        await self.update_consumption_point_in_time(
            consumption_context,
            consumption_context.previous_consumption_date,
            total_counter - current_day_value,
        )

        logger.debug("Handled midnight case")
