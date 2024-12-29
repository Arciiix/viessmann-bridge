from datetime import date
from urllib.parse import unquote_plus
import aiohttp
from viessmann_bridge.logger import logger
from viessmann_bridge.action import Action
from viessmann_bridge.config import HomeAssistantActionConfig
from viessmann_bridge.consumption import ConsumptionContext


class HomeAssistant(Action):
    config: HomeAssistantActionConfig

    def __init__(self, config: HomeAssistantActionConfig) -> None:
        self.config = config

    async def init(self) -> None:
        pass

    async def _request(self, endpoint: str, data: dict) -> None:
        logger.debug(
            f"Requesting Home Assistant {self.config.home_assistant_url} with data: {data}"
        )

        headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                f"{self.config.home_assistant_url}/{endpoint}", data=data
            ) as response:
                logger.debug(unquote_plus(str(response.request_info.real_url)))

                if response.status == 200:
                    logger.debug(f"Response: {await response.text()}")
                else:
                    logger.error(
                        f"Failed to request Home Assistant {self.config.home_assistant_url}: {response.status}"
                    )

    async def update_current_total_consumption(
        self,
        consumption_context: ConsumptionContext,
        total_consumption: int,
        today: int,
    ) -> None:
        logger.debug(f"Updating current total consumption: {total_consumption}")

        if self.config.gas_usage_entity_id is not None:
            await self._request(
                f"api/states/{self.config.gas_usage_entity_id}",
                {
                    "state": str(total_consumption),
                    "attributes": {
                        "unit_of_measurement": "kWh",
                    },
                },
            )

        raise NotImplementedError()

    async def update_current_total_consumption_increasing(
        self, consumption_context: ConsumptionContext, consumption_increase_offset: int
    ) -> None:
        pass

    async def update_daily_consumption_stats(
        self, consumption_context: ConsumptionContext, consumption: dict[date, int]
    ):
        # TODO: Research how to implement this in the future
        pass

    async def handle_consumption_midnight_case(
        self,
        consumption_context: ConsumptionContext,
        previous_day_new_value: int,
        offset_previous_day: int,
        current_day_value: int,
        total_counter: int,
    ):
        await self.update_current_total_consumption(
            consumption_context, total_counter, current_day_value
        )

    async def handle_burners_modulations(self, burners_modulations: list[int]):
        logger.debug(f"Handling burners modulations: {burners_modulations}")

        for entity, modulation in zip(
            self.config.burner_modulation_entities_ids, burners_modulations
        ):
            await self._request(
                f"api/states/{entity}",
                {
                    "state": str(modulation),
                    "attributes": {
                        "unit_of_measurement": "%",
                    },
                },
            )

    async def handle_boiler_temperature(self, boiler_temperature: float):
        logger.debug(f"Handling boiler temperature: {boiler_temperature}")

        if self.config.boiler_temperature_entity_id is not None:
            await self._request(
                f"api/states/{self.config.boiler_temperature_entity_id}",
                {
                    "state": str(boiler_temperature),
                    "attributes": {"unit_of_measurement": "°C"},
                },
            )
