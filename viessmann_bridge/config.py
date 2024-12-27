from typing import Literal, Optional, Union
from zoneinfo import ZoneInfo
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as

from viessmann_bridge.logger import logger


class ViessmannCreds(BaseModel):
    username: str
    password: str
    client_id: str


class Action(BaseModel):
    action_type: str


class DomoticzAction(Action):
    action_type: Literal["domoticz"]

    domoticz_url: str

    boiler_temp_idx: Optional[int] = None
    burner_modulation_idx: Optional[int] = None
    gas_consumption_m3_idx: Optional[int] = None
    gas_consumption_kwh_idx: Optional[int] = None


class HomeAssistantAction(Action):
    action_type: Literal["home_assistant"]

    home_assistant_url: str


class Config(BaseModel):
    timezone: ZoneInfo
    viessmann_creds: ViessmannCreds
    device_index: int = 0

    actions: list[Union[DomoticzAction, HomeAssistantAction]] = []


GlobalConfig: Optional[Config] = None


def get_config() -> Config:
    if GlobalConfig is None:
        raise ValueError("Config not loaded")
    return GlobalConfig


def load_config() -> Config:
    global GlobalConfig

    if GlobalConfig is not None:
        logger.info("Config already loaded")

    try:
        with open("config.yaml", "r") as f:
            config = parse_yaml_raw_as(Config, f.read())
            GlobalConfig = config

            logger.info("Config loaded")
            return config
    except FileNotFoundError as e:
        logger.error("Config file not found")
        raise e
