from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel

from viessmann_bridge.logger import logger
from viessmann_bridge.consumption import ConsumptionContext


class ActionConfig(BaseModel):
    action_type: str


class DomoticzActionConfig(ActionConfig):
    action_type: Literal["domoticz"]

    domoticz_url: str

    # If true, uses ?type=devices instead of ?type=command&param=getdevices
    # Applies to Domoticz before 01.06.2023, please see: https://github.com/domoticz/domoticz-android/issues/692
    use_legacy_device_endpoint: bool = False

    boiler_temp_idx: Optional[int] = None
    burner_modulation_idx: Optional[int] = None
    gas_consumption_m3_idx: Optional[int] = None
    gas_consumption_kwh_idx: Optional[int] = None

    gas_consumption_m3_increasing_idx: Optional[int] = None
    gas_consumption_kwh_increasing_idx: Optional[int] = None


class HomeAssistantActionConfig(ActionConfig):
    action_type: Literal["home_assistant"]

    home_assistant_url: str


class Action:
    """
    Action class serves as a base class with virtual methods that are intended to be overridden by subclasses.
    """

    async def init(self) -> None:
        """
        Initialize the action
        """
        raise NotImplementedError()

    async def update_current_total_consumption(
        self,
        consumption_context: ConsumptionContext,
        total_consumption: int,
    ) -> None:
        """
        Update the current total consumption

        Args:
            consumption_context (ConsumptionContext): Consumption context
            total_consumption (int): Gas consumption in kWh
        """
        logger.debug(f"Updating current total consumption: {total_consumption}")
        raise NotImplementedError()

    async def update_current_total_consumption_incresing(
        self, consumption_context: ConsumptionContext, consumption_increase_offset: int
    ) -> None:
        """
        Update the current total consumption by increasing the previous value.

        The difference between this method and update_current_total_consumption is that
        this method just 'adds' the new consumption to the previous value, while the
        update_current_total_consumption method overrides the total consumption value.

        Args:
            consumption_context (ConsumptionContext): Consumption context
            consumption_increase_offset (int): = new total consumption - previous total consumption
        """
        logger.debug(
            f"Updating current total consumption increasing: {consumption_increase_offset}"
        )
        raise NotImplementedError()

    async def update_daily_consumption_stats(
        self, consumption_context: ConsumptionContext, consumption: dict[date, int]
    ):
        """
        Update the daily consumption stats

        Args:
            consumption_context (ConsumptionContext): Consumption context
            consumption (dict[date, int]): Gas consumption in kWh for each day
        """
        logger.debug(f"Updating daily consumption stats: {consumption}")
        raise NotImplementedError()

    async def handle_consumption_midnight_case(
        self,
        consumption_context: ConsumptionContext,
        previous_day_new_value: int,
        offset_previous_day: int,
        current_day_value: int,
        total_counter: int,
    ):
        """
        Handle the case when the counter resets at midnight.

        Viessmann API updates are surely not "realtime", meaning that really often
        when the midnight comes, the counter is not updated yet (and a new day is not started).
        And then when the daily usage is updated, a new day appears, but the previous
        day's value can be changed in the meantime between the updates.

        Args:
            consumption_context (ConsumptionContext): Consumption context
            previous_day_new_value (int): New value for the previous day, updated
            offset_previous_day (int): Offset for the previous day (how much the value differs from the previous value)
            current_day_value (int): Current day value
            total_counter (int): Total counter value
        """
        logger.debug(f"""
Handling midnight case with the following values:
    previous_day_new_value: {previous_day_new_value},
    offset_previous_day: {offset_previous_day},
    current_day_value: {current_day_value},
    total_counter: {total_counter}
""")
        raise NotImplementedError()
