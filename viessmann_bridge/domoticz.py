from viessmann_bridge.action import Action
from viessmann_bridge.config import DomoticzActionConfig


class Domoticz(Action):
    config: DomoticzActionConfig

    def __init__(self, config: DomoticzActionConfig) -> None:
        self.config = config
