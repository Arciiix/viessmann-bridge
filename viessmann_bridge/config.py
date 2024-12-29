from typing import Optional, Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as

from viessmann_bridge.action import (
    Action,
    DomoticzActionConfig,
    HomeAssistantActionConfig,
)
from viessmann_bridge.domoticz import Domoticz
from viessmann_bridge.home_assistant import HomeAssistant
from viessmann_bridge.logger import logger


class ViessmannCreds(BaseModel):
    username: str
    password: str
    client_id: str


class Config(BaseModel):
    timezone: ZoneInfo
    sleep_interval_seconds: int = 300
    viessmann_creds: ViessmannCreds
    device_index: int = 0
    number_of_burners: int = 1

    actions: list[Union[DomoticzActionConfig, HomeAssistantActionConfig]] = []


GlobalConfig: Optional[Config] = None
GlobalActions: list[Action] = []


def get_config() -> Config:
    if GlobalConfig is None:
        raise ValueError("Config not loaded")
    return GlobalConfig


def get_actions() -> list[Action]:
    if not GlobalActions:
        raise ValueError("Actions not loaded")
    return GlobalActions


async def load_config() -> Config:
    global GlobalConfig

    if GlobalConfig is not None:
        logger.info("Config already loaded")

    try:
        with open("config.yaml", "r") as f:
            config = parse_yaml_raw_as(Config, f.read())
            GlobalConfig = config

            for action in GlobalConfig.actions:
                new_action: Optional[Action] = None

                if isinstance(action, DomoticzActionConfig):
                    new_action = Domoticz(action)
                elif isinstance(action, HomeAssistantActionConfig):
                    new_action = HomeAssistant(action)

                if new_action is not None:
                    GlobalActions.append(new_action)
                    logger.info(f"Added action: {type(new_action)}")

                    await new_action.init()
                    logger.info(f"Action {type(new_action)} initialized")
                else:
                    logger.warning(f"Unknown action type: {action.action_type}")

            logger.info("Config loaded")
            return config
    except FileNotFoundError as e:
        logger.error("Config file not found")
        raise e
