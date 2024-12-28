import asyncio

from viessmann_bridge.config import load_config
from viessmann_bridge.logger import logger
from viessmann_bridge.vicare_api import init_vicare_device
from viessmann_bridge.work import ViessmannBridge


def main():
    logger.info("Starting viessmann_bridge")

    config = asyncio.run(load_config())
    device = init_vicare_device(config)

    bridge = ViessmannBridge(device)
    asyncio.run(bridge.main_loop())


if __name__ == "__main__":
    main()
