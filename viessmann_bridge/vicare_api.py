from PyViCare.PyViCare import PyViCare
from PyViCare.PyViCareGazBoiler import GazBoiler

from viessmann_bridge.logger import logger
from viessmann_bridge.config import Config
from viessmann_bridge.device import Device


def init_vicare_device(config: Config) -> Device:
    client = PyViCare()
    client.initWithCredentials(
        config.viessmann_creds.username,
        config.viessmann_creds.password,
        config.viessmann_creds.client_id,
        "token.save",
    )

    device_obj = client.devices[config.device_index]
    logger.info(
        f"Connected to device {device_obj.getModel()}. It's currently {'online' if device_obj.isOnline() else 'offline'}"
    )

    # Ensure it's a gas boiler as we only support gas boilers for now
    auto_device = device_obj.asAutoDetectDevice()

    if not isinstance(auto_device, GazBoiler):
        raise ValueError("Device is not a Gas Boiler")

    device = Device(auto_device)
    return device
