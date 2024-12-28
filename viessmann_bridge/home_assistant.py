from viessmann_bridge.action import Action
from viessmann_bridge.config import HomeAssistantActionConfig


class HomeAssistant(Action):
    config: HomeAssistantActionConfig

    def __init__(self, config: HomeAssistantActionConfig) -> None:
        self.config = config

    async def init(self) -> None:
        pass
