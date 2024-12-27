import asyncio

from viessmann_bridge.config import load_config
from viessmann_bridge.logger import logger
from viessmann_bridge.vicare_api import init_vicare_device
from viessmann_bridge.work import main_loop


def main():
    logger.info("Starting viessmann_bridge")

    config = load_config()
    device = init_vicare_device(config)

    asyncio.run(main_loop(device))


if __name__ == "__main__":
    main()
