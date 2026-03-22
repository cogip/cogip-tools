from pathlib import Path

from cogip.scservo_async_sdk import SCServoDriver


async def get_driver(port: Path, baud_rate: int) -> SCServoDriver:
    driver = SCServoDriver(str(port), baud_rate)
    await driver.open()
    return driver
