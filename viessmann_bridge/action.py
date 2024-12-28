from datetime import date

from viessmann_bridge.consumption import ConsumptionContext


class Action:
    """
    Action class serves as a base class with virtual methods that are intended to be overridden by subclasses.
    """

    def update_current_total_consumption(
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
        raise NotImplementedError()

    def update_daily_consumption_stats(
        self, consumption_context: ConsumptionContext, consumption: dict[date, int]
    ):
        """
        Update the daily consumption stats

        Args:
            consumption_context (ConsumptionContext): Consumption context
            consumption (dict[date, int]): Gas consumption in kWh for each day
        """
        raise NotImplementedError()
